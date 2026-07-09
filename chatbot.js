const RAG_BACKEND_URL = 'https://your-rag-backend.example.com';
const USE_RAG_BACKEND = false;

const portfolioBotKnowledge = [
  {
    keywords: ['project', 'projects', 'portfolio', 'github', 'repo', 'repositories'],
    answer: `My portfolio focuses on practical Data & AI projects: Bank Term Deposit Prediction for classical ML, Athens Fuel Prices ETL for data engineering, IMDB Sentiment Analysis for NLP, and Procurement Analytics & AI Enablement for business-oriented AI work. You can explore the repositories from the Projects section or GitHub button.`
  },
  {
    keywords: ['skill', 'skills', 'python', 'sql', 'power bi', 'pandas', 'dax'],
    answer: `My strongest working toolkit is Python, SQL, Pandas, NumPy, Power BI, Excel, DAX, KPI design, and data modeling. I group my skills by depth so recruiters can quickly see what I use daily versus what I am actively developing.`
  },
  {
    keywords: ['ml', 'machine learning', 'model', 'classification', 'regression', 'scikit'],
    answer: `For Machine Learning, I focus on the full classical ML workflow: feature engineering, classification, regression, model comparison, evaluation, and business interpretation. The Bank Term Deposit project is the main example.`
  },
  {
    keywords: ['rag', 'llm', 'nlp', 'ai', 'chatbot', 'assistant', 'agent'],
    answer: `My AI direction includes RAG systems, LLM workflows, document-aware assistants, prompt engineering, embeddings, and AI apps. I am especially interested in AI systems that help business users retrieve knowledge and complete workflows. A RAG backend scaffold has been added so this chatbot can answer from actual GitHub project documentation once deployed.`
  },
  {
    keywords: ['data engineering', 'etl', 'postgresql', 'sqlite', 'pipeline', 'automation'],
    answer: `On the data engineering side, I work with ETL, PostgreSQL, SQLite, data validation, automation, and reproducible project structure. The Athens Fuel Prices ETL project is a good example of this direction.`
  },
  {
    keywords: ['experience', 'work', 'ppc', 'procurement', 'sap', 'ariba', 's4hana'],
    answer: `Professionally, I work around procurement transformation, SAP Ariba, SAP S/4HANA, reporting, UAT, data validation, stakeholder enablement, Power BI dashboards, automation, and applied AI experimentation.`
  },
  {
    keywords: ['economics', 'background', 'story', 'about'],
    answer: `My path started from Economics, where I learned to think about systems, incentives, constraints, and measurable outcomes. I then moved into Python, SQL, Power BI, ML, and AI Engineering to build practical systems that support decisions.`
  },
  {
    keywords: ['contact', 'email', 'linkedin', 'hire', 'opportunity', 'opportunities'],
    answer: `You can contact me by email at dimmark995@gmail.com, connect with me on LinkedIn, or explore my work on GitHub. Use the Contact section or the floating Contact button on this page.`
  },
  {
    keywords: ['cv', 'resume'],
    answer: `A dedicated CV download button is a good next improvement for this portfolio. For now, the best contact paths are LinkedIn, GitHub, and email.`
  }
];

const fallbackAnswers = [
  `I can help you quickly understand Dimitrios' skills, projects, AI direction, professional experience, and contact options. Try asking: "What projects has he built?"`,
  `Good question. This portfolio bot has a RAG backend scaffold ready. Until the backend is deployed, I answer from local portfolio knowledge.`,
  `Try one of these topics: projects, skills, machine learning, RAG, data engineering, procurement analytics, or contact.`
];

async function askRagBackend(question) {
  if (!USE_RAG_BACKEND || !RAG_BACKEND_URL || RAG_BACKEND_URL.includes('example.com')) {
    return null;
  }

  const response = await fetch(`${RAG_BACKEND_URL.replace(/\/$/, '')}/api/chat`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ message: question, top_k: 5 })
  });

  if (!response.ok) {
    throw new Error(`RAG backend returned ${response.status}`);
  }

  const data = await response.json();
  return data.answer;
}

function getLocalBotAnswer(question) {
  const normalized = question.toLowerCase();
  const match = portfolioBotKnowledge.find(item =>
    item.keywords.some(keyword => normalized.includes(keyword))
  );

  if (match) {
    return match.answer;
  }

  return fallbackAnswers[Math.floor(Math.random() * fallbackAnswers.length)];
}

function createPortfolioChatbot() {
  const launcher = document.createElement('button');
  launcher.className = 'chatbot-launcher';
  launcher.type = 'button';
  launcher.setAttribute('aria-label', 'Open portfolio chatbot');
  launcher.innerHTML = '🤖 Ask me';

  const panel = document.createElement('section');
  panel.className = 'chatbot-panel';
  panel.setAttribute('aria-label', 'Portfolio chatbot');
  panel.innerHTML = `
    <div class="chatbot-header">
      <div class="chatbot-title">
        <div class="chatbot-avatar">DM</div>
        <div>
          <strong>Portfolio Assistant</strong>
          <span>Ask about skills, projects, AI work or contact</span>
        </div>
      </div>
      <button class="chatbot-close" type="button" aria-label="Close chatbot">×</button>
    </div>
    <div class="chatbot-messages" aria-live="polite"></div>
    <div class="chatbot-suggestions" aria-label="Suggested questions">
      <button class="chatbot-chip" type="button">Projects</button>
      <button class="chatbot-chip" type="button">Skills</button>
      <button class="chatbot-chip" type="button">RAG & LLMs</button>
      <button class="chatbot-chip" type="button">Contact</button>
    </div>
    <form class="chatbot-form">
      <input class="chatbot-input" type="text" placeholder="Ask about my portfolio..." autocomplete="off" aria-label="Ask the portfolio chatbot" />
      <button class="chatbot-send" type="submit">Send</button>
    </form>
  `;

  document.body.appendChild(panel);
  document.body.appendChild(launcher);

  const messages = panel.querySelector('.chatbot-messages');
  const closeButton = panel.querySelector('.chatbot-close');
  const form = panel.querySelector('.chatbot-form');
  const input = panel.querySelector('.chatbot-input');
  const chips = panel.querySelectorAll('.chatbot-chip');

  function addMessage(text, sender = 'bot') {
    const message = document.createElement('div');
    message.className = `chat-message ${sender}`;
    message.textContent = text;
    messages.appendChild(message);
    messages.scrollTop = messages.scrollHeight;
    return message;
  }

  async function askBot(question) {
    const cleanQuestion = question.trim();
    if (!cleanQuestion) return;

    addMessage(cleanQuestion, 'user');
    input.value = '';
    const loadingMessage = addMessage('Searching Dimitrios\' project knowledge...', 'bot');

    try {
      const ragAnswer = await askRagBackend(cleanQuestion);
      loadingMessage.textContent = ragAnswer || getLocalBotAnswer(cleanQuestion);
    } catch (error) {
      console.warn('RAG backend unavailable, using local fallback:', error);
      loadingMessage.textContent = getLocalBotAnswer(cleanQuestion);
    }

    messages.scrollTop = messages.scrollHeight;
  }

  function openChat() {
    panel.classList.add('open');
    launcher.setAttribute('aria-label', 'Close portfolio chatbot');
    window.setTimeout(() => input.focus(), 120);
  }

  function closeChat() {
    panel.classList.remove('open');
    launcher.setAttribute('aria-label', 'Open portfolio chatbot');
  }

  launcher.addEventListener('click', () => {
    if (panel.classList.contains('open')) {
      closeChat();
    } else {
      openChat();
    }
  });

  closeButton.addEventListener('click', closeChat);

  form.addEventListener('submit', event => {
    event.preventDefault();
    askBot(input.value);
  });

  chips.forEach(chip => {
    chip.addEventListener('click', () => askBot(chip.textContent));
  });

  document.addEventListener('keydown', event => {
    if (event.key === 'Escape' && panel.classList.contains('open')) {
      closeChat();
      launcher.focus();
    }
  });

  addMessage(`Hi, I am Dimitrios' portfolio assistant. Ask me about projects, skills, RAG/LLMs, data engineering, procurement analytics, or how to contact him.`);
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', createPortfolioChatbot);
} else {
  createPortfolioChatbot();
}
