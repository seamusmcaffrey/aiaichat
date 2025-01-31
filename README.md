# 🦜 Parrot AI Thinktank

A collaborative AI discussion platform that enables multiple AI models to analyze and debate coding problems together. The system facilitates structured conversations between different AI models, each taking on specialized roles to provide comprehensive solutions.

## 🚀 Features

- Multi-model AI discussions with Claude, GPT-4, and DeepSeek
- Role-based interactions with AI experts
- File upload support for code analysis
- Interactive conversation flow
- Consensus generation
- Customizable discussion rounds
- Code syntax highlighting
- Mobile-responsive design

## 📋 Prerequisites

- Python 3.8+
- Streamlit
- API keys for the AI services you want to use (Claude, GPT-4, and/or DeepSeek)
- Git (for cloning the repository)

## 🛠️ Installation

1. Clone the repository:
```bash
git clone https://github.com/seamusmcaffrey/parrot
cd parrot
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## 🔑 API Key Configuration

The app uses Streamlit's secrets management for API keys. You need to create a `secrets.toml` file in the `.streamlit` directory of your project:

1. Create the secrets file:
```bash
mkdir -p .streamlit
touch .streamlit/secrets.toml
```

→ Alternatively, you can navigate to https://share.streamlit.io/ → My apps → 3-dot menu next to your chatbot → Settings → Add your own secret keys

2. Add your API keys to `secrets.toml`:
```toml
# .streamlit/secrets.toml

CLAUDE_API_KEY = "your-anthropic-api-key"
OPENAI_API_KEY = "your-openai-api-key"
DEEPSEEK_API_KEY = "your-deepseek-api-key"
```

### Getting API Keys

- **Claude**: Sign up at [Anthropic](https://www.anthropic.com/) and obtain an API key
- **GPT-4**: Get your API key from [OpenAI](https://platform.openai.com/account/api-keys)
- **DeepSeek**: Register at [DeepSeek](https://platform.deepseek.com/) for an API key

## 🚀 Running the App

1. Start the Streamlit app:
## 🚀 Running the App

### Option 1: Run Locally

1. Open a terminal and navigate to the project directory:
   ```bash
   cd parrot

	2.	Start the Streamlit app:

streamlit run app.py


	3.	Open your browser and navigate to the URL displayed in the terminal (usually http://localhost:8501).

Option 2: Deploy on Streamlit Cloud

You can also host Parrot AI Thinktank on Streamlit Community Cloud to make it accessible online.

Step 1: Sign in to Streamlit
	1.	Go to Streamlit Community Cloud.
	2.	Click “Sign in” (using GitHub or Google).

Step 2: Create a New App
	1.	Click “Deploy an app” on the Streamlit dashboard.
	2.	Under “Repository”, enter your GitHub repository URL:

https://github.com/seamusmcaffrey/parrot


	3.	Select the main branch and set app.py as the main file.
	4.	Click “Deploy”.

Step 3: Configure Secrets for API Keys

To add API keys securely:
	1.	In the Streamlit dashboard, find your deployed app.
	2.	Click the three-dot menu (⋮) next to the app → “Settings”.
	3.	Select “Secrets” and add the API keys:

CLAUDE_API_KEY = "your-anthropic-api-key"
OPENAI_API_KEY = "your-openai-api-key"
DEEPSEEK_API_KEY = "your-deepseek-api-key"


	4.	Click “Save”.

Step 4: Launch Your App
	•	Once deployed, Streamlit will provide a public URL for your app.
	•	Share this link to allow others to interact with Parrot AI Thinktank.



2. Open your browser and navigate to the URL shown in the terminal (usually `http://localhost:8501`)

## 💡 Usage

1. **Select AI Models**: Choose at least two AI models from the sidebar
2. **Upload Code** (Optional): Attach relevant code files for analysis
3. **Describe Problem**: Enter your coding problem or question
4. **Set Rounds**: Adjust the number of discussion rounds
5. **Start Discussion**: Click the "Start AI Discussion" button
6. **View Results**: Read the AI experts' analysis and final consensus
7. **Copy Consensus**: Use the copy button to save the final consensus

## 🔒 Security Notes

- Never commit your `secrets.toml` file to version control
- Add `.streamlit/secrets.toml` to your `.gitignore` file
- Keep your API keys secure and rotate them periodically
- Monitor your API usage to manage costs

## 🐛 Troubleshooting

Common issues and solutions:

1. **API Key Errors**:
   - Verify your API keys are correctly formatted in `secrets.toml`
   - Check that the keys have the necessary permissions
   - Ensure you have sufficient API credits

2. **Model Selection Issues**:
   - At least two models must be selected
   - Verify API keys are configured for selected models

3. **File Upload Problems**:
   - Check that file type is supported
   - Ensure file size is under 200MB
   - Verify file encoding is UTF-8

## 📚 Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## 🙏 Acknowledgments

- Built with [Streamlit](https://streamlit.io/)
- AI services provided by [Anthropic](https://www.anthropic.com/), [OpenAI](https://openai.com/), and [DeepSeek](https://deepseek.com/)

## 📧 Support

Comment on the git and I'll do my best!