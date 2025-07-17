// quiz.js 法律答题前端逻辑

// 禁止页面滚动
if (document.body) {
  document.body.style.overflow = 'hidden';
} else {
  window.addEventListener('DOMContentLoaded', function() {
    document.body.style.overflow = 'hidden';
  });
}

document.addEventListener('DOMContentLoaded', function() {
  // 只在法律答题页面初始化
  if (!document.getElementById('page-quiz')) return;

  // DOM元素
  const quizPage = document.getElementById('page-quiz');
  const questionTitle = quizPage.querySelector('.quiz-question-title');
  const optionsList = quizPage.querySelector('.quiz-options');
  const answerBox = quizPage.querySelector('.answer-content');
  const submitBtn = quizPage.querySelector('.quiz-submit-btn');

  let currentQuestion = null;
  let selected = null;

  // 加载题目
  async function loadQuiz() {
    const res = await fetch('http://127.0.0.1:8000/quiz');
    const data = await res.json();
    quizList = data;
    currentIdx = 0;
    if (quizList.length > 0) {
      currentQuestion = quizList[0];
      renderQuiz(currentQuestion);
    }
  }

  // 渲染题目和选项
  function renderQuiz(q) {
    questionTitle.textContent = q.question;
    optionsList.innerHTML = '';
    q.options.forEach((opt, idx) => {
      const li = document.createElement('li');
      li.innerHTML = `<input type="radio" name="quiz-option" id="option${idx}"><label for="option${idx}">${opt}</label>`;
      optionsList.appendChild(li);
    });
    answerBox.textContent = '请作答后显示答案';
    selected = null;
    // 绑定选项事件
    optionsList.querySelectorAll('input[type=radio]').forEach((input, idx) => {
      input.onclick = () => { selected = idx; };
    });
  }

  // 提交答案
  submitBtn.onclick = async function() {
    if (selected === null) {
      answerBox.textContent = '请先选择一个选项';
      return;
    }
    const originalText = submitBtn.textContent;
    submitBtn.textContent = '加载中...';
    submitBtn.disabled = true;
    try {
      const res = await fetch('http://127.0.0.1:8000/quiz/answer', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ id: currentQuestion.id, answer: selected })
      });
      const data = await res.json();
      if (data.correct) {
        answerBox.textContent = '回答正确！';
      } else {
        answerBox.textContent = `回答错误，正确答案是：${currentQuestion.options[data.correct_answer]}`;
      }
      if (data.explanation) {
        answerBox.textContent += `\n解析：${data.explanation}`;
      }
    } finally {
    submitBtn.textContent = originalText;
    submitBtn.disabled = false;
  }
  };

  // 右下角折角点击加载下一题
  const nextCorner = document.querySelector('.corner.right-corner');
  let quizList = [];
  let currentIdx = 0;

  if (nextCorner) {
    nextCorner.style.cursor = 'pointer';
    nextCorner.title = '点击进入下一题';
    nextCorner.onclick = function() {
      if (quizList.length === 0) return;
      currentIdx = (currentIdx + 1) % quizList.length;
      currentQuestion = quizList[currentIdx];
      renderQuiz(currentQuestion);
    };
  }

  // 初始化
  loadQuiz();
}); 