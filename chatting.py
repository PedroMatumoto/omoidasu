import openai
from dotenv import find_dotenv, load_dotenv

_ = load_dotenv(find_dotenv())

client = openai.OpenAI()


def chat(
    messages: list,
    model: str = "gpt-4o-mini",
    temperature: float = 0.0,
    stream: bool = False,
) -> str:
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        stream=stream,
    )
    return response.choices[0].message.content


# messages = [
#     {"role": "user", "content": "Me fale uma receita que use manga."},
# ]

# response = chat(messages)
# print(response)

# messages.append(
#     {"role": "assistant", "content": response},
# )

# messages.append({"role": "user", "content": "Essa fruta é saudável?"})

# response = chat(messages)
# print(response)
