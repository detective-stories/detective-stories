choose_story = "🕵️‍♂️ Choose a Detective Story"

story_start_md = """
*📜 {title}*

{description}
""".strip()

story_lobby_md = """
You are solving the mystery of *🕵️‍♂️ {title}*.

Choose a character to interrogate.

If you're ready to reveal your solution, type /verdict 🕵️‍♂️

To exit the story, type /quit 🚪
""".strip()

agent_selected_md = """
You are now interrogating *🕵️‍♂️ {agent_name}*

Type your message or send a voice message.

To return to the characters list, type /back 🔙
""".strip()

agent_partial_answer_html = """
🕵️‍♂️ <b>{agent_name}</b> is saying...

<i>{agent_answer}</i>
""".strip()

agent_full_answer_html = """
🕵️‍♂️ <b>{agent_name}</b> says:

<i>{agent_answer}</i>

To go back to the characters list, type /back 🔙
""".strip()

agent_thinking_html = """
<b>🕵️‍♂️ {agent_name}</b> is thinking... ⏳
""".strip()

agent_failure_html = """
<b>🕵️‍♂️ {agent_name}</b> is unable to answer your question.

Please try again later.

To go back to the characters list, type /back 🔙
""".strip()

ask_for_verdict_md = """
You are about to reveal your verdict 🕵️‍♂️

Type your solution.

To go back to the characters list, type /back 🔙
""".strip()

verdict_md = """
Your verdict:
_{player_verdict}_

Author verdict:
_{system_verdict}_

The system has decided that your solution is *{correctness}* 🧐.

Thank you for playing! 🎉
""".strip()

verdict_succes = """
System assessment of your answer:

Person(s): {person}
Motivation: {motivation}
Way the crime was committed: {way}

The story is complete! 🎉🎉🎉
"""

verdict_failure = """
System assessment of your answer:

Person(s): {person}
Motivation: {motivation}
Way the crime was committed: {way}

The story is not complete. 🤔

Hint: {hint}
"""

quit_md = """
You have exited the mystery. 🚪🔍
""".strip()

correct = "correct ✅"
incorrect = "incorrect ❌"

loading_answer = "Loading answer... ⏳"

start_md = """
🕵️‍♂️ **Welcome to Detective Story Bot!**

Embark on thrilling detective adventures and put your sleuthing skills to the test. To get started:

1. Use the command /list to view available detective stories.
2. Select a story by choosing its title.
3. Follow the prompts to solve the mystery and deliver your verdict with /verdict.

Type /help at any time for a list of available commands and guidance.

Get ready to uncover secrets and solve crimes! 🔍🕵️‍♂️
""".strip()

help_md = """
🕵️‍♂️ **Detective Story Bot Help**

Welcome to the Detective Story Bot! Here are the available commands:

1. /list - View available detective stories and choose one to solve.
2. /help - Display this help message.

During a story:
- Engage with characters by selecting them or typing your messages.
- Use /verdict to deliver your solution and find out if you cracked the case! 🕵️‍♂️
- Use /back to return to the character list or the previous step.
- Exit the current detective story using /quit.

Remember, to select your next adventure and explore available stories, use /list.

The key to success is in the details! Happy sleuthing! 🔍🎩
""".strip()

unknown_command_md = """
Sorry, I don't understand. 🤔

Type /help to see the list of available commands. 🕵️‍♂️
""".strip()

audio_too_large_md = """
Sorry, the audio file is too large. Please send a shorter audio message. 🎤
""".strip()

unknown_callback = """
❌ Sorry, this button is no longer available. 🤔
""".strip()
