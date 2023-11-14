choose_story = '🕵️‍♂️ Choose a Detective Story'

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

Type your message.

To return to the character list, type /back 🔙
""".strip()

agent_answer_md = """
*🕵️‍♂️ {agent_name}* says:

_{agent_answer}_

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

quit_md = """
You have exited the mystery. 🚪🔍
""".strip()

correct = 'correct ✅'
incorrect = 'incorrect ❌'

loading_answer = 'Loading answer... ⏳'

start_md = """
🕵️‍♂️ **Welcome to Detective Story Bot!**

Embark on thrilling detective adventures and put your sleuthing skills to the test. To get started:

1. Use the command /list to view available detective stories.
2. Select a story by choosing its corresponding number.
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

Remember, to select your next adventure, use /list. If you want to explore available stories, try /list.

The key to success is in the details! Happy sleuthing! 🔍🎩
""".strip()