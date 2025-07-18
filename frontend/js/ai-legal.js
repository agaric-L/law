// AI懂法历史侧栏逻辑
function toggleHistorySidebar() {
  document.getElementById('historySidebar').classList.add('open');
  renderHistory();
}

function closeHistorySidebar() {
  document.getElementById('historySidebar').classList.remove('open');
}

function getHistory() {
  return JSON.parse(localStorage.getItem('ai_legal_history') || '[]');
}

function saveHistory(history) {
  localStorage.setItem('ai_legal_history', JSON.stringify(history));
}

function addToHistory(item) {
  const history = getHistory();
  history.unshift(item);
  saveHistory(history);
}

function renderHistory() {
  const list = document.getElementById('historyList');
  const history = getHistory();
  const search = document.getElementById('historySearch').value.trim();
  list.innerHTML = '';
  history.filter(h => !search || h.question.includes(search)).forEach(h => {
    const div = document.createElement('div');
    div.className = 'history-item';
    div.innerText = h.question;
    div.onclick = () => {
      document.getElementById('userInput').value = h.question;
      closeHistorySidebar();
    };
    list.appendChild(div);
  });
}

function fillAndSend(text) {
  document.getElementById('userInput').value = text;
  sendQuestion();
}

let currentModel = '通义千问'; // 统一用后端识别的英文key

function toggleModelMenu() {
  const menu = document.getElementById('modelMenu');
  menu.style.display = (menu.style.display === 'none' || menu.style.display === '') ? 'block' : 'none';
}

function selectModel(model) {
  currentModel = model;
  let showName = model;
  if(model==='通义千问') showName='通义千问';
  if(model==='星火大模型') showName='星火大模型';
  if(model==='deepseek') showName='DeepSeek';
  if(model==='智谱') showName='智谱';
  document.getElementById('currentModel').innerText = '当前模型：' + showName;
  document.getElementById('modelMenu').style.display = 'none';
}

async function sendQuestion() {
  const input = document.getElementById('userInput');
  const question = input.value.trim();
  if (!question) return;
  appendChatBubble('user', question);
  input.value = '';

  // 新增流式fetch
  const chat = document.getElementById('chatHistory');
  // 先插入一个空的AI气泡
  const wrapper = document.createElement('div');
  wrapper.className = 'chat-bubble-wrapper ai';
  const avatar = document.createElement('img');
  avatar.className = 'chat-avatar';
  avatar.src = 'image/律师.png';
  avatar.alt = '律师头像';
  const bubble = document.createElement('div');
  bubble.className = 'chat-bubble ai';
  bubble.innerHTML = '';
  wrapper.appendChild(avatar);
  wrapper.appendChild(bubble);
  chat.appendChild(wrapper);
  chat.scrollTop = chat.scrollHeight;

  // fetch流式
  const response = await fetch('http://127.0.0.1:8000/ai_legal_qa/stream', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question, model: currentModel })
  });
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let result = '';
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    const text = decoder.decode(value, { stream: true });
    result += text;
    bubble.innerHTML = result.replace(/\n/g, '<br>');
    chat.scrollTop = chat.scrollHeight;
  }
  // 可选：流式结束后，保存历史
  addToHistory({ question, answer: result });
}

function appendChatBubble(role, text) {
  const chat = document.getElementById('chatHistory');
  // 创建外层容器
  const wrapper = document.createElement('div');
  wrapper.className = 'chat-bubble-wrapper ' + role;

  // 创建头像
  const avatar = document.createElement('img');
  avatar.className = 'chat-avatar';
  if (role === 'user') {
    avatar.src = 'image/用户.png';
    avatar.alt = '用户头像';
  } else {
    avatar.src = 'image/律师.png';
    avatar.alt = '律师头像';
  }

  // 创建气泡内容
  const bubble = document.createElement('div');
  bubble.className = 'chat-bubble ' + role;
  bubble.innerHTML = text.replace(/\n/g, '<br>');

  // AI：头像在气泡前面（左侧）；用户：头像在气泡后面（右侧）
  if (role === 'ai') {
    wrapper.appendChild(avatar);
    wrapper.appendChild(bubble);
  } else {
    wrapper.appendChild(bubble);
    wrapper.appendChild(avatar);
  }

  chat.appendChild(wrapper);
  chat.scrollTop = chat.scrollHeight;
}

function startNewConversation() {
  document.getElementById('chatHistory').innerHTML = '';
  fetch('http://127.0.0.1:8000/reset_ai_memory', { method: 'POST' })
  .then(() => {
    // 可以在这里解锁输入框，允许用户输入新问题
  });
}

// 初始化AI懂法功能
function initAILegal() {
  // 绑定历史搜索事件
  const historySearch = document.getElementById('historySearch');
  if (historySearch) {
    historySearch.oninput = renderHistory;
  }
  
  // 绑定模型菜单点击事件
  document.body.addEventListener('click', function(e) {
    if (!e.target.closest('#modelBtn') && !e.target.closest('#modelMenu')) {
      document.getElementById('modelMenu').style.display = 'none';
    }
  });
  
  // 绑定回车发送事件
  const userInput = document.getElementById('userInput');
  if (userInput) {
    userInput.addEventListener('keydown', function(e) {
      if (e.key === 'Enter') {
        sendQuestion();
      }
    });
  }
}

// 页面加载完成后初始化AI懂法功能
document.addEventListener('DOMContentLoaded', function() {
  initAILegal();
}); 
