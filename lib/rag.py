import lancedb
from lancedb.rerankers import RRFReranker
from langfuse import Langfuse, observe
from langfuse.openai import OpenAI


class RAG:
    def __init__(self, model="gpt-4o", temperature=0.6):
        self.db = lancedb.connect("db")
        self.table = self.db.open_table("molrag")
        self.reranker = RRFReranker()
        self.client_settings = {
            "model": model,
            "temperature": temperature,
        }
        self.client = OpenAI()
        self.langfuse = Langfuse(blocked_instrumentation_scopes=["chainlit"])
        self.langfuse_prompt = self.langfuse.get_prompt("Simple Q&A prompt")

        # self.table.create_fts_index("text", replace=True)

    @observe()
    def get_context(self, query: str, num_results: int = 8):
        """Search the database for relevant context.

        Args:
            query: User's question
            table: LanceDB table object
            num_results: Number of results to return

        Returns:
            str: Concatenated context from relevant chunks with source information
        """

        # Sanitize the query to handle apostrophes and backticks
        # TODO: Find a more robust solution
        sanitized_query = query.replace("'", "").replace("`", "")

        results = (
            self.table.search(
                sanitized_query,
                query_type="hybrid",
                vector_column_name="vector",
                fts_columns="text",
            )
            .rerank(self.reranker)
            .limit(num_results)
            .to_pandas()
        )

        contexts = []

        for _, row in results.iterrows():
            context = "<document>"

            url = row["metadata"]["url"]
            title = row["metadata"]["page_title"]
            source = row["metadata"]["source"]

            if title:
                context += f"\nTitle: {title}"

            if source:
                context += f"\nSource: {source}"

            if url:
                context += f"\nURL: {url}"

            contexts.append(context + "\nContent: " + row["text"] + "\n</document>\n")

        final_context = "\n\n".join(contexts)

        return [final_context, results]

    @observe()
    def evaluate_context_and_relevance(self, query: str, context: str) -> str:
        """Evaluate if the retrieved context is sufficient and/or if the query is relevant to Molecule/DeSci.

        Args:
            query: User's question
            context: Retrieved context from the knowledge base

        Returns:
            str: One of "SUFFICIENT", "INSUFFICIENT_BUT_RELEVANT", "INSUFFICIENT_AND_IRRELEVANT"
        """

        print(
            f"🔍 [DEBUG] Evaluating context sufficiency and relevance for query: '{query[:100]}...'"
        )

        langfuse_eval_prompt = self.langfuse.get_prompt("Local-Or-Websearch-Eval")
        compiled_eval_prompt = langfuse_eval_prompt.compile(
            query=query, context=context
        )

        messages = [
            {
                "role": "user",
                "content": compiled_eval_prompt,
            }
        ]

        response = self.client.chat.completions.create(
            messages=messages,
            model="gpt-4o",
            temperature=0.1,  # Low temperature for consistent evaluation
            max_tokens=50,  # Allow slightly more tokens for reasoning
            langfuse_prompt=langfuse_eval_prompt,
        )

        result = response.choices[0].message.content.strip().upper()

        # Remove quotes if present and ensure we get a valid response
        result = result.strip('"').strip("'")

        # Ensure we get a valid response, default to INSUFFICIENT_AND_IRRELEVANT if unclear
        if result not in [
            "SUFFICIENT",
            "INSUFFICIENT_BUT_RELEVANT",
            "INSUFFICIENT_AND_IRRELEVANT",
        ]:
            print(
                f"⚠️ [DEBUG] Unexpected evaluation result: {result}, defaulting to INSUFFICIENT_AND_IRRELEVANT"
            )
            result = "INSUFFICIENT_AND_IRRELEVANT"

        print(f"📊 [DEBUG] Context and relevance evaluation result: {result}")

        return result

    @observe()
    def generate_web_search_answer(
        self, query: str, message_history: list = None
    ) -> str:
        """Generate an answer using OpenAI's web search when local context is insufficient.

        Args:
            query: User's question
            message_history: Previous conversation messages

        Returns:
            str: Answer generated using web search
        """

        print(f"🔎 [DEBUG] Performing web search for query: '{query[:100]}...'")

        # Ensure message_history is a list and handle None case
        if message_history is None:
            message_history = []

        print(f"🔍 [DEBUG] Web search message history length: {len(message_history)}")

        websearch_prompt = self.langfuse.get_prompt("Websearch-Prompt")
        compiled_websearch_prompt = websearch_prompt.compile(
            query=query,
        )

        # Prepare messages: include conversation history if available
        messages = []
        if message_history and len(message_history) > 0:
            # Validate message history format
            for msg in message_history:
                if isinstance(msg, dict) and "role" in msg and "content" in msg:
                    messages.append(msg)
                else:
                    print(f"⚠️ [DEBUG] Skipping invalid message in history: {msg}")

        messages.append(
            {
                "role": "user",
                "content": compiled_websearch_prompt,
            }
        )

        response = self.client.chat.completions.create(
            model="gpt-4o-search-preview",
            web_search_options={},
            messages=messages,
            langfuse_prompt=websearch_prompt,
        )

        answer = response.choices[0].message.content

        # Log annotations if present
        trusted_domains = [
            "molecule.to",
            "molecule.xyz",
            "bio.xyz",
            "vitadao.com",
        ]
        trusted_sources = []

        if (
            hasattr(response.choices[0].message, "annotations")
            and response.choices[0].message.annotations
        ):
            print(
                f"📎 [DEBUG] Found {len(response.choices[0].message.annotations)} annotations in web search response:"
            )
            for i, annotation in enumerate(response.choices[0].message.annotations):
                if annotation.type == "url_citation" and hasattr(
                    annotation, "url_citation"
                ):
                    citation = annotation.url_citation
                    print(f"  📌 Citation {i + 1}:")
                    print(f"     - URL: {citation.url}")
                    print(f"     - Title: {citation.title}")
                    print(
                        f"     - Text range: [{citation.start_index}:{citation.end_index}]"
                    )

                    # Check if the citation is from a trusted domain
                    from urllib.parse import urlparse

                    parsed_url = urlparse(citation.url)
                    domain = parsed_url.netloc.lower()

                    # Remove www. prefix if present
                    if domain.startswith("www."):
                        domain = domain[4:]

                    if any(trusted in domain for trusted in trusted_domains):
                        trusted_sources.append(
                            {
                                "url": citation.url,
                                "title": citation.title,
                                "start_index": citation.start_index,
                                "end_index": citation.end_index,
                                "domain": domain,
                            }
                        )
                        print(f"     ✅ TRUSTED DOMAIN: {domain}")
                    else:
                        print(f"     ❌ UNTRUSTED DOMAIN: {domain}")
        else:
            print("📎 [DEBUG] No annotations found in web search response")

        print(
            f"✨ [DEBUG] Web search completed, found {len(trusted_sources)} trusted sources"
        )

        # Filter the answer to only include information from trusted sources
        if trusted_sources:
            # Create a filter prompt to rewrite the answer with only trusted sources
            filter_prompt = """You are tasked with filtering an answer to only include information that can be verified from trusted sources.

You have been provided with:
1. An original answer that may contain information from various sources
2. A list of TRUSTED sources that you should use
3. The original user query

Your task is to rewrite the answer to ONLY include information that can be attributed to the trusted sources listed below.

IMPORTANT RULES:
- Only include facts, claims, or information that come from the trusted sources
- Do not include any information from sources not in the trusted list
- Maintain the helpful tone and structure of the original answer
- If the trusted sources don't contain enough information to fully answer the query, acknowledge this limitation
- Always cite the trusted sources when making claims

TRUSTED SOURCES:
{trusted_sources}

ORIGINAL QUERY:
{query}

ORIGINAL ANSWER TO FILTER:
{original_answer}

Please provide a filtered answer that only uses information from the trusted sources listed above:"""

            # Prepare the trusted sources information
            trusted_sources_text = "\n".join(
                [f"- {source['title']} ({source['url']})" for source in trusted_sources]
            )

            compiled_filter_prompt = filter_prompt.format(
                original_answer=answer,
                trusted_sources=trusted_sources_text,
                query=query,
            )

            filter_messages = [{"role": "user", "content": compiled_filter_prompt}]

            filter_response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=filter_messages,
                temperature=0.3,
            )

            filtered_answer = filter_response.choices[0].message.content
            print("🔐 [DEBUG] Answer filtered to include only trusted sources")

            return filtered_answer
        else:
            # No trusted sources found, return a message indicating this
            no_trusted_info_message = (
                "Sorry, I couldn't find any information from trusted sources "
                "regarding your question."
            )
            print("⚠️ [DEBUG] No trusted sources found, returning default message")
            return no_trusted_info_message

    @observe()
    def generate_answer(self, query: str, message_history: list = None):
        """Generate an answer using agentic RAG approach.

        Args:
            query: User's question
            message_history: Previous conversation messages

        Returns:
            tuple: (answer, context_data, used_web_search)
        """
        print(f"🚀 [DEBUG] Starting agentic RAG for query: '{query[:100]}...'")

        # Ensure message_history is a list and handle None case
        if message_history is None:
            message_history = []

        print(f"🔍 [DEBUG] Message history length: {len(message_history)}")

        # First, get context from local knowledge base
        context_data = self.get_context(query)
        context_str = context_data[0]

        print(
            f"📚 [DEBUG] Retrieved {len(context_data[1])} documents from local knowledge base"
        )

        # Evaluate if context is sufficient and relevant
        result = self.evaluate_context_and_relevance(query, context_str)

        if result == "SUFFICIENT":
            print("✅ [DEBUG] Using LOCAL RAG - context is sufficient")
            # Use local RAG approach
            dynamic_system_prompt = self.langfuse_prompt.compile(context=context_str)

            # Prepare messages: system prompt + conversation history + current user message
            messages = [{"role": "system", "content": dynamic_system_prompt}]

            # Add conversation history if available and valid
            if message_history and len(message_history) > 0:
                for msg in message_history:
                    if isinstance(msg, dict) and "role" in msg and "content" in msg:
                        messages.append(msg)
                    else:
                        print(f"⚠️ [DEBUG] Skipping invalid message in history: {msg}")

            messages.append({"role": "user", "content": query})

            response = self.client.chat.completions.create(
                messages=messages,
                **self.client_settings,
            )

            answer = response.choices[0].message.content
            return answer, context_data, False
        elif result == "INSUFFICIENT_BUT_RELEVANT":
            print(
                "🌐 [DEBUG] Using WEB SEARCH - local context is insufficient but relevant"
            )
            # Use web search
            answer = self.generate_web_search_answer(query, message_history)
            return answer, context_data, True
        else:  # INSUFFICIENT_AND_IRRELEVANT
            print("📝 [DEBUG] Question appears outside scope - returning fixed message")
            # Return fixed message for irrelevant questions
            answer = "Sorry, I can't help you with that question"
            return answer, context_data, False
