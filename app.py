import streamlit as st
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote
from streamlit_mic_recorder import speech_to_text
from gtts import gTTS
import tempfile
import os


# =========================================================
# PAGE SETUP
# =========================================================

st.set_page_config(
    page_title="Infobox Explorer",
    page_icon="🔎",
    layout="wide",
    initial_sidebar_state="expanded"
)


# =========================================================
# SESSION STATE
# =========================================================

defaults = {
    "history": [],
    "bookmarks": [],
    "search_results": [],
    "article_title": "",
    "article_text": "",
    "wiki_url": "",
    "image_url": "",
    "infobox": [],
    "related": [],
    "chat": [],
    "last_answer": ""
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


# =========================================================
# GEMMA
# =========================================================

def ask_gemma(prompt):

    try:

        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "gemma2:2b",
                "prompt": prompt,
                "stream": False
            },
            timeout=120
        )

        response.raise_for_status()

        data = response.json()

        return data.get(
            "response",
            "No response received."
        )

    except requests.exceptions.ConnectionError:

        return (
            "❌ Gemma is not running. "
            "Please start Ollama."
        )

    except requests.exceptions.Timeout:

        return (
            "⏳ Gemma took too long to respond."
        )

    except Exception as error:

        return "❌ AI Error: " + str(error)


# =========================================================
# TEXT TO SPEECH
# =========================================================

def create_audio(text):

    try:

        file = tempfile.NamedTemporaryFile(
            delete=False,
            suffix=".mp3"
        )

        path = file.name
        file.close()

        tts = gTTS(
            text=text,
            lang="en"
        )

        tts.save(path)

        return path

    except Exception:

        return None


# =========================================================
# CLEAR ARTICLE
# =========================================================

def clear_article():

    st.session_state.article_title = ""
    st.session_state.article_text = ""
    st.session_state.wiki_url = ""
    st.session_state.image_url = ""
    st.session_state.infobox = []
    st.session_state.related = []
    st.session_state.chat = []
    st.session_state.last_answer = ""


# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:

    st.title("🔎 Infobox Explorer")

    st.write(
        "Search, explore and learn with AI."
    )

    st.divider()

    st.subheader("🤖 AI Status")

    if st.button(
        "🟢 Check Gemma",
        use_container_width=True
    ):

        with st.spinner("Checking Gemma..."):

            answer = ask_gemma(
                "Reply with only READY."
            )

        if "READY" in answer.upper():

            st.success(
                "Gemma is ready!"
            )

        else:

            st.error(answer)

    st.divider()

    st.subheader("⭐ Bookmarks")

    if st.session_state.bookmarks:

        for item in st.session_state.bookmarks:

            st.write("⭐ " + item)

        if st.button(
            "🗑️ Clear Bookmarks",
            use_container_width=True
        ):

            st.session_state.bookmarks = []

            st.rerun()

    else:

        st.info(
            "No bookmarked articles."
        )

    st.divider()

    st.subheader("🕘 Recent Searches")

    if st.session_state.history:

        for item in st.session_state.history[:10]:

            st.write("🔹 " + item)

        if st.button(
            "🗑️ Clear History",
            use_container_width=True
        ):

            st.session_state.history = []

            st.rerun()

    else:

        st.info(
            "No search history."
        )


# =========================================================
# HEADER
# =========================================================

st.title("🔎 Infobox Explorer")

st.write(
    "A Wikipedia exploration tool powered by "
    "Python, Streamlit and Gemma AI."
)


# =========================================================
# DASHBOARD
# =========================================================

st.subheader("🏠 Dashboard")

c1, c2, c3, c4 = st.columns(4)

with c1:

    st.metric(
        "🔎 Searches",
        len(st.session_state.history)
    )

with c2:

    st.metric(
        "⭐ Bookmarks",
        len(st.session_state.bookmarks)
    )

with c3:

    st.metric(
        "📚 Results",
        len(st.session_state.search_results)
    )

with c4:

    st.metric(
        "📖 Current Article",
        "Loaded"
        if st.session_state.article_title
        else "None"
    )


# =========================================================
# SEARCH
# =========================================================

st.divider()

st.subheader("🔍 Search Wikipedia")

topic = st.text_input(
    "What do you want to learn about?",
    placeholder="Example: Artificial Intelligence"
)

if st.button(
    "🔎 Search Wikipedia",
    use_container_width=True
):

    if not topic.strip():

        st.warning(
            "Please enter a topic."
        )

    else:

        try:

            response = requests.get(
                "https://en.wikipedia.org/w/api.php",
                params={
                    "action": "query",
                    "list": "search",
                    "srsearch": topic,
                    "srlimit": 8,
                    "format": "json"
                },
                headers={
                    "User-Agent": "InfoboxExplorer/15.0"
                },
                timeout=15
            )

            response.raise_for_status()

            data = response.json()

            results = data.get(
                "query",
                {}
            ).get(
                "search",
                []
            )

            if not results:

                st.warning(
                    "No Wikipedia article found."
                )

            else:

                st.session_state.search_results = results

                if topic not in st.session_state.history:

                    st.session_state.history.insert(
                        0,
                        topic
                    )

                st.session_state.history = (
                    st.session_state.history[:10]
                )

                st.success(
                    f"✅ Found {len(results)} results."
                )

        except Exception as error:

            st.error(
                "❌ Search failed."
            )

            st.write(str(error))


# =========================================================
# RESULTS
# =========================================================

if st.session_state.search_results:

    st.divider()

    st.subheader("📚 Wikipedia Results")

    titles = [
        item["title"]
        for item in st.session_state.search_results
    ]

    selected_title = st.selectbox(
        "Choose an article",
        titles
    )

    selected_item = next(
        (
            item
            for item in st.session_state.search_results
            if item["title"] == selected_title
        ),
        None
    )

    if selected_item:

        snippet = BeautifulSoup(
            selected_item.get(
                "snippet",
                ""
            ),
            "html.parser"
        ).get_text(
            " ",
            strip=True
        )

        st.info(
            "📌 " + snippet
        )

    if st.button(
        "📖 Open Selected Article",
        use_container_width=True
    ):

        try:

            wiki_url = (
                "https://en.wikipedia.org/wiki/"
                + quote(
                    selected_title.replace(
                        " ",
                        "_"
                    )
                )
            )

            response = requests.get(
                wiki_url,
                headers={
                    "User-Agent": "InfoboxExplorer/15.0"
                },
                timeout=20
            )

            response.raise_for_status()

            soup = BeautifulSoup(
                response.text,
                "html.parser"
            )

            # TITLE

            st.session_state.article_title = (
                selected_title
            )

            st.session_state.wiki_url = wiki_url

            # ARTICLE TEXT

            paragraphs = soup.find_all("p")

            texts = []

            for paragraph in paragraphs:

                text = paragraph.get_text(
                    " ",
                    strip=True
                )

                if text:

                    texts.append(text)

            st.session_state.article_text = (
                "\n\n".join(texts[:10])
            )

            # IMAGE + INFOBOX

            st.session_state.infobox = []

            st.session_state.image_url = ""

            infobox = soup.find(
                "table",
                class_="infobox"
            )

            if infobox:

                image = infobox.find("img")

                if image:

                    image_url = image.get(
                        "src",
                        ""
                    )

                    if image_url.startswith("//"):

                        image_url = (
                            "https:" + image_url
                        )

                    st.session_state.image_url = (
                        image_url
                    )

                for row in infobox.find_all("tr"):

                    heading = row.find("th")
                    value = row.find("td")

                    if heading and value:

                        key = heading.get_text(
                            " ",
                            strip=True
                        )

                        val = value.get_text(
                            " ",
                            strip=True
                        )

                        if key and val:

                            st.session_state.infobox.append(
                                (key, val)
                            )

            # RELATED ARTICLES

            st.session_state.related = []

            for link in soup.find_all(
                "a",
                href=True
            ):

                text = link.get_text(
                    " ",
                    strip=True
                )

                href = link.get("href")

                if (
                    text
                    and href
                    and href.startswith("/wiki/")
                    and ":" not in href
                ):

                    item = (
                        text,
                        "https://en.wikipedia.org" + href
                    )

                    if item not in st.session_state.related:

                        st.session_state.related.append(
                            item
                        )

                if len(
                    st.session_state.related
                ) >= 15:

                    break

            st.session_state.chat = []

            st.session_state.last_answer = ""

            st.success(
                "✅ Article loaded successfully!"
            )

        except Exception as error:

            st.error(
                "❌ Unable to load article."
            )

            st.write(str(error))


# =========================================================
# ARTICLE DISPLAY
# =========================================================

if st.session_state.article_title:

    title = st.session_state.article_title

    article = st.session_state.article_text

    st.divider()

    st.header(
        "📖 " + title
    )

    # BOOKMARK

    if title in st.session_state.bookmarks:

        if st.button("⭐ Remove Bookmark"):

            st.session_state.bookmarks.remove(
                title
            )

            st.rerun()

    else:

        if st.button("⭐ Bookmark Article"):

            st.session_state.bookmarks.append(
                title
            )

            st.success(
                "⭐ Article bookmarked!"
            )

    st.link_button(
        "🌐 Open Full Wikipedia Article",
        st.session_state.wiki_url
    )

    # IMAGE AND SUMMARY

    left, right = st.columns(
        [1, 2]
    )

    with left:

        if st.session_state.image_url:

            st.image(
                st.session_state.image_url,
                caption=title,
                use_container_width=True
            )

        else:

            st.info(
                "🖼️ No image available."
            )

    with right:

        st.subheader(
            "📌 Quick Overview"
        )

        if article:

            st.write(
                article.split("\n\n")[0]
            )

    # =====================================================
    # TABS
    # =====================================================

    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs(
        [
            "📖 Article",
            "📋 Infobox",
            "🤖 AI Assistant",
            "🎤 Voice",
            "🔗 Related",
            "📊 Statistics",
            "ℹ️ About Project"
        ]
    )


    # =====================================================
    # ARTICLE TAB
    # =====================================================

    with tab1:

        st.subheader(
            "📚 Article Content"
        )

        st.write(article)

        st.download_button(
            "📥 Download Article",
            data=article,
            file_name=(
                title.replace(
                    " ",
                    "_"
                )
                + ".txt"
            ),
            mime="text/plain"
        )


    # =====================================================
    # INFOBOX TAB
    # =====================================================

    with tab2:

        st.subheader(
            "📋 Infobox Information"
        )

        if st.session_state.infobox:

            for key, value in (
                st.session_state.infobox
            ):

                st.markdown(
                    "**" + key + "**"
                )

                st.write(value)

                st.divider()

        else:

            st.info(
                "No infobox available."
            )


    # =====================================================
    # AI TAB
    # =====================================================

    with tab3:

        st.subheader(
            "🤖 Gemma AI Assistant"
        )

        col1, col2 = st.columns(2)

        with col1:

            if st.button(
                "✨ Generate Summary"
            ):

                prompt = f"""
You are an educational AI assistant.

Article title:
{title}

Article:
{article}

Create a simple summary.

Include:
1. Main idea
2. Important facts
3. Applications
4. Conclusion

Use easy language.
"""

                with st.spinner(
                    "🤖 Gemma is working..."
                ):

                    answer = ask_gemma(
                        prompt
                    )

                st.session_state.last_answer = answer

                st.markdown(
                    "### ✨ AI Summary"
                )

                st.write(answer)

        with col2:

            if st.button(
                "🧠 Key Points"
            ):

                prompt = f"""
Read this article.

{article}

Give 10 important points
using short and simple sentences.
"""

                with st.spinner(
                    "🧠 Generating..."
                ):

                    answer = ask_gemma(
                        prompt
                    )

                st.session_state.last_answer = answer

                st.markdown(
                    "### 🧠 Key Points"
                )

                st.write(answer)

        st.divider()

        st.subheader(
            "💬 Ask Gemma"
        )

        for message in st.session_state.chat:

            with st.chat_message(
                message["role"]
            ):

                st.write(
                    message["content"]
                )

        question = st.chat_input(
            "Ask something about this article..."
        )

        if question:

            st.session_state.chat.append(
                {
                    "role": "user",
                    "content": question
                }
            )

            prompt = f"""
You are helping a college student.

Article:
{article}

Question:
{question}

Answer using simple language.
Only use information related to the article.
"""

            with st.spinner(
                "🤖 Gemma is thinking..."
            ):

                answer = ask_gemma(
                    prompt
                )

            st.session_state.chat.append(
                {
                    "role": "assistant",
                    "content": answer
                }
            )

            st.session_state.last_answer = answer

            st.rerun()


    # =====================================================
    # VOICE TAB
    # =====================================================

    with tab4:

        st.subheader(
            "🎤 Voice Assistant"
        )

        st.write(
            "Ask a question using your microphone."
        )

        spoken_text = speech_to_text(
            language="en",
            start_prompt="🎤 Start Speaking",
            stop_prompt="⏹️ Stop",
            just_once=True,
            use_container_width=True,
            key="voice_v15"
        )

        if spoken_text:

            st.success(
                "🎤 You said:"
            )

            st.write(
                spoken_text
            )

            prompt = f"""
Article:
{article}

User question:
{spoken_text}

Answer simply and clearly.
"""

            with st.spinner(
                "🤖 Gemma is answering..."
            ):

                answer = ask_gemma(
                    prompt
                )

            st.session_state.last_answer = answer

            st.subheader(
                "🤖 Gemma Answer"
            )

            st.write(answer)

        st.divider()

        if st.session_state.last_answer:

            if st.button(
                "🔊 Read Answer Aloud"
            ):

                with st.spinner(
                    "🔊 Creating audio..."
                ):

                    audio_path = create_audio(
                        st.session_state.last_answer
                    )

                if audio_path:

                    with open(
                        audio_path,
                        "rb"
                    ) as audio_file:

                        st.audio(
                            audio_file.read(),
                            format="audio/mp3"
                        )

                    try:

                        os.remove(audio_path)

                    except Exception:

                        pass

                else:

                    st.error(
                        "Unable to create audio."
                    )

        else:

            st.info(
                "Generate an AI answer first."
            )


    # =====================================================
    # RELATED TAB
    # =====================================================

    with tab5:

        st.subheader(
            "🔗 Related Wikipedia Articles"
        )

        if st.session_state.related:

            for text, url in (
                st.session_state.related
            ):

                st.markdown(
                    f"- [{text}]({url})"
                )

        else:

            st.info(
                "No related articles found."
            )


    # =====================================================
    # STATISTICS
    # =====================================================

    with tab6:

        st.subheader(
            "📊 Article Statistics"
        )

        words = len(
            article.split()
        )

        characters = len(article)

        paragraphs = len(
            article.split("\n\n")
        )

        infobox_items = len(
            st.session_state.infobox
        )

        related = len(
            st.session_state.related
        )

        a, b, c, d, e = st.columns(5)

        with a:

            st.metric(
                "📝 Words",
                words
            )

        with b:

            st.metric(
                "🔤 Characters",
                characters
            )

        with c:

            st.metric(
                "📚 Paragraphs",
                paragraphs
            )

        with d:

            st.metric(
                "📋 Infobox Items",
                infobox_items
            )

        with e:

            st.metric(
                "🔗 Related",
                related
            )


    # =====================================================
    # ABOUT PROJECT
    # =====================================================

    with tab7:

        st.subheader(
            "ℹ️ About Infobox Explorer"
        )

        st.write(
            """
Infobox Explorer is a Python-based educational
web application that allows users to search and
explore Wikipedia articles.

The application combines Wikipedia data with
Gemma 2B local AI to help users understand
articles in simple language.
"""
        )

        st.subheader(
            "🎯 Project Objectives"
        )

        st.write(
            """
• Search Wikipedia articles easily

• Display article summaries and infobox details

• Provide AI-generated explanations

• Allow users to ask questions about articles

• Provide voice-based interaction

• Show article statistics

• Save useful articles as bookmarks
"""
        )

        st.subheader(
            "🛠️ Technologies Used"
        )

        st.write(
            """
🐍 Python

🎈 Streamlit

🌐 Wikipedia API

📄 BeautifulSoup

🤖 Gemma 2B

🦙 Ollama

🎤 Speech Recognition

🔊 Text-to-Speech
"""
        )

        st.subheader(
            "🚀 Future Scope"
        )

        st.write(
            """
• Multi-language support

• More AI models

• Cloud deployment

• User accounts

• Advanced article comparison

• Educational quiz generation
"""
        )


# =========================================================
# FOOTER
# =========================================================

st.divider()

st.caption(
    "Infobox Explorer | Version 15 | "
    "Final Project | Python + Streamlit + Wikipedia + "
    "Gemma 2B + Ollama + Voice AI"
)