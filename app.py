import uuid

import chainlit as cl
from langfuse import Langfuse, observe
from langfuse.openai import AsyncOpenAI

from lib.rag import RAG

rag = RAG()

knowledge_version = "knowledge-2025-08-19"

client = AsyncOpenAI()

langfuse = Langfuse(blocked_instrumentation_scopes=["chainlit"])

client_settings = {
    "model": "gpt-4o",
    "temperature": 0.3,
}


@cl.action_callback("thumbs_up_button")
async def on_thumbs_up(action):
    langfuse.create_score(
        trace_id=action.payload["trace_id"],
        name="user_feedback_helpful",
        value=1,
        data_type="BOOLEAN",
    )

    # Remove both thumbs up and thumbs down actions after rating
    trace_id = action.payload["trace_id"]
    stored_actions = cl.user_session.get("feedback_actions", {})
    if trace_id in stored_actions:
        for stored_action in stored_actions[trace_id]:
            await stored_action.remove()
        # Clean up the stored actions for this trace
        del stored_actions[trace_id]
        cl.user_session.set("feedback_actions", stored_actions)


@cl.action_callback("thumbs_down_button")
async def on_thumbs_down(action):
    langfuse.create_score(
        trace_id=action.payload["trace_id"],
        name="user_feedback_helpful",
        value=0,
        data_type="BOOLEAN",
    )

    # Remove both thumbs up and thumbs down actions after rating
    trace_id = action.payload["trace_id"]
    stored_actions = cl.user_session.get("feedback_actions", {})
    if trace_id in stored_actions:
        for stored_action in stored_actions[trace_id]:
            await stored_action.remove()
        # Clean up the stored actions for this trace
        del stored_actions[trace_id]
        cl.user_session.set("feedback_actions", stored_actions)


@cl.set_starters
async def set_starters():
    return [
        cl.Starter(
            label="Learn about DeSci and Molecule",
            message="What is DeSci all about, and what does Molecule do?",
            icon="/public/icons/mol.svg",
        ),
        cl.Starter(
            label="Fund and advance your research",
            message="What DeSci tools and Molecule products can I use to fund and advance my research?",
            icon="/public/icons/fund.svg",
        ),
        cl.Starter(
            label="Tokenize your intellectual property",
            message="What does it mean to tokenize my IP, and how do I start?",
            icon="/public/icons/minter_2.svg",
        ),
    ]


@cl.on_chat_start
def start_chat():
    cl.user_session.set("uuid", str(uuid.uuid4()))
    cl.user_session.set(
        "message_history",
        [],  # Initialize with an empty list
    )
    cl.user_session.set("feedback_actions", {})  # Initialize feedback actions storage


@cl.on_message
@observe()
async def handle_message(message: cl.Message):
    # Show thinking indicator
    thinking_msg = cl.Message(content="🤔 Thinking...")
    await thinking_msg.send()

    langfuse.update_current_trace(
        input=message.content,
        session_id=cl.user_session.get("uuid"),
        tags=[knowledge_version],
    )

    # get current trace id
    trace_id = langfuse.get_current_trace_id()

    # Get message history before calling RAG
    message_history = cl.user_session.get("message_history", [])

    # Ensure message_history is always a list
    if not isinstance(message_history, list):
        message_history = []

    print(f"🔍 [DEBUG] Current message history length: {len(message_history)}")

    # Show debug message about starting agentic RAG
    # debug_msg = cl.Message(
    #     content="🔄 **[DEBUG]** Starting Enhanced Agentic RAG process...\n\n1. 📚 Retrieving context from local knowledge base\n2. 🤔 Evaluating context sufficiency and topic relevance\n3. 🎯 Routing decision: Local RAG vs Web Search vs Out-of-scope"
    # )
    # await debug_msg.send()

    # Agentic RAG: Get answer using the new approach
    answer, context_data, used_web_search = rag.generate_answer(
        message.content, message_history
    )
    context_str = context_data[0]  # The first element is the context string
    db_results = context_data[1]

    # Update debug message with decision
    # if used_web_search:
    #     debug_msg.content = "🔄 **[DEBUG]** Enhanced Agentic RAG Decision: **WEB SEARCH** 🌐\n\n✅ Process completed:\n1. 📚 Retrieved context from local knowledge base\n2. 🤔 Evaluated: Context insufficient BUT topic relevant\n3. 🌐 Using web search for current information"
    #     await debug_msg.update()
    # else:
    #     # Check if this was a disclaimer case by looking at the answer content
    #     if "outside" in answer.lower() and "expertise" in answer.lower():
    #         debug_msg.content = "🔄 **[DEBUG]** Enhanced Agentic RAG Decision: **LOCAL RAG + DISCLAIMER** ⚠️\n\n✅ Process completed:\n1. 📚 Retrieved context from local knowledge base\n2. 🤔 Evaluated: Context insufficient AND topic not relevant\n3. 📝 Using local knowledge with scope disclaimer"
    #     else:
    #         debug_msg.content = "🔄 **[DEBUG]** Enhanced Agentic RAG Decision: **LOCAL RAG** ✅\n\n✅ Process completed:\n1. 📚 Retrieved context from local knowledge base\n2. 🤔 Evaluated: Context sufficient for this topic\n3. 📖 Using local knowledge base"
    #     await debug_msg.update()

    langfuse.update_current_trace(
        metadata={"context": context_str, "used_web_search": used_web_search}
    )

    # Prepare sources display based on decision
    if used_web_search:
        sources = "**Information retrieved from web search** 🌐\n *This answer was generated using current web search results as the local knowledge base didn't contain sufficient information for this Molecule/DeSci-related question.*\n\n\n"
        # Add a note about web search being used
        langfuse.update_current_trace(tags=[knowledge_version, "web-search-used"])
    else:
        # Check if this was a disclaimer case
        if "outside" in answer.lower() and "expertise" in answer.lower():
            sources = "**Information from local knowledge base (with disclaimer)** ⚠️\n *This question appears to be outside the primary scope of Molecule and DeSci topics. The response is based on limited available information.*\n\n"
            for _, row in db_results.iterrows():
                sources += f"**{row['metadata']['page_title']}** \n {row['metadata']['url']} \n *Source: {row['metadata']['source']}*\n\n\n"
            langfuse.update_current_trace(
                tags=[knowledge_version, "out-of-scope-disclaimer"]
            )
        else:
            sources = "**Information from local knowledge base** 📚\n"
            for _, row in db_results.iterrows():
                sources += f"**{row['metadata']['page_title']}** \n {row['metadata']['url']} \n *Source: {row['metadata']['source']}*\n\n\n"
            # Add a note about local knowledge being used
            langfuse.update_current_trace(
                tags=[knowledge_version, "local-knowledge-used"]
            )

    # Used to debug, hide for now
    # elements = [cl.Text(name="Sources", content=sources, display="inline")]

    # Sending action buttons within chatbot message
    actions = [
        cl.Action(
            name="thumbs_up_button",
            payload={"trace_id": trace_id},
            icon="thumbs-up",
        ),
        cl.Action(
            name="thumbs_down_button",
            payload={"trace_id": trace_id},
            icon="thumbs-down",
        ),
    ]

    # Store actions in user session for later removal
    stored_actions = cl.user_session.get("feedback_actions", {})
    stored_actions[trace_id] = actions
    cl.user_session.set("feedback_actions", stored_actions)

    # Remove thinking indicator before sending actual response
    await thinking_msg.remove()

    # For web search, we already have the complete answer
    if used_web_search:
        msg = cl.Message(content=answer, elements=[], actions=actions)
        await msg.send()
    else:
        # For local RAG, use streaming as before
        # Get prompt from Langfuse
        langfuse_prompt = langfuse.get_prompt("Simple Q&A prompt")

        # Create dynamic system prompt
        dynamic_system_prompt = langfuse_prompt.compile(context=context_str)

        # Prepare messages for API call: dynamic system prompt + history + current user message
        api_messages = (
            [{"role": "system", "content": dynamic_system_prompt}]
            + message_history
            + [{"role": "user", "content": message.content}]
        )

        msg = cl.Message(content="", elements=[], actions=actions)

        stream = await client.chat.completions.create(
            messages=api_messages,
            stream=True,
            langfuse_prompt=langfuse_prompt,  # capture used prompt version in trace
            **client_settings,
        )

        async for part in stream:
            if token := part.choices[0].delta.content or "":
                await msg.stream_token(token)

    # Update message history with the user's current message and the assistant's response
    # Ensure we have valid content before adding to history
    assistant_content = msg.content if msg.content else ""

    updated_history = message_history + [
        {"role": "user", "content": message.content},
        {"role": "assistant", "content": assistant_content},
    ]

    print(f"🔍 [DEBUG] Updated message history length: {len(updated_history)}")
    cl.user_session.set("message_history", updated_history)

    langfuse.update_current_trace(output=msg.content)

    if not used_web_search:
        await msg.update()
