// ========== 全局变量与初始化 ==========
let currentStage = null;
let currentRole = null;
let userRole = 'plaintiff'; // 用户选择的角色
let courtSessionStarted = false;
let evidenceList = {
  plaintiff: [],
  defendant: []
};

// 页面加载后初始化
window.addEventListener('DOMContentLoaded', function() {
  initCourt();
});

document.addEventListener('DOMContentLoaded', function() {
  var quickBtn = document.getElementById('quick-fill-btn');
  if (quickBtn) {
    quickBtn.addEventListener('click', function() {
      document.getElementById('case-summary').value = '原告与被告因借款发生纠纷，被告未按约定归还借款，现提起诉讼。';
      document.getElementById('plaintiff-claim').value = '请求判令被告归还借款本金10万元及利息。';
      document.getElementById('plaintiff-reason').value = '原告与被告签订借款协议，原告已履行出借义务，被告未按约定还款，依法应承担还款责任。';
      document.getElementById('plaintiff-evidence-text').value = '1. 借款协议书；2. 银行转账凭证。';
      // 若证据描述textarea是隐藏的，可以显示它
      var evidenceText = document.getElementById('plaintiff-evidence-text');
      if (evidenceText && evidenceText.style.display === 'none') {
        evidenceText.style.display = '';
      }
      // 被告部分
      document.getElementById('defendant-opinion').value = '不同意原告诉讼请求，请求法院驳回。';
      document.getElementById('defendant-reason').value = '原告所述借款事实不属实，被告未收到相关款项。';
      document.getElementById('defendant-evidence-text').value = '1. 银行流水；2. 通讯记录。';
      var defEvidenceText = document.getElementById('defendant-evidence-text');
      if (defEvidenceText && defEvidenceText.style.display === 'none') {
        defEvidenceText.style.display = '';
      }
    });
  }
});

function initCourt() {
  // 角色选择
  document.querySelectorAll('input[name="role"]').forEach(radio => {
    radio.addEventListener('change', function() {
      userRole = this.value;
    });
  });
  // 证据上传按钮事件
  document.getElementById('plaintiff-evidence-file').addEventListener('change', function(e) {
    handleFileUpload(e, 'plaintiff');
  });
  document.getElementById('defendant-evidence-file').addEventListener('change', function(e) {
    handleFileUpload(e, 'defendant');
  });
  // 文字证据按钮事件
  document.getElementById('plaintiff-evidence-text-btn').addEventListener('click', function() {
    toggleTextEvidence('plaintiff');
  });
  document.getElementById('defendant-evidence-text-btn').addEventListener('click', function() {
    toggleTextEvidence('defendant');
  });
  // 开始庭审
  document.getElementById('start-trial-btn').addEventListener('click', startTrial);
  // 发送消息
  document.getElementById('send-court-message-btn').addEventListener('click', sendCourtMessage);
  // 新庭审
  document.getElementById('new-trial-btn').addEventListener('click', startNewTrial);
}

// ========== 证据管理 ==========
function handleFileUpload(event, role) {
  const files = event.target.files;
  if (!files || files.length === 0) return;
  for (let i = 0; i < files.length; i++) {
    const file = files[i];
    evidenceList[role].push({
      type: 'file',
      name: file.name,
      file: file
    });
  }
  event.target.value = '';
  updateEvidenceList(role);
}

function toggleTextEvidence(role) {
  const textArea = document.getElementById(`${role}-evidence-text`);
  if (textArea.style.display === 'none') {
    textArea.style.display = 'block';
    textArea.focus();
    textArea.onblur = function() {
      if (textArea.value.trim()) {
        evidenceList[role].push({
          type: 'text',
          content: textArea.value.trim()
        });
        textArea.value = '';
        textArea.style.display = 'none';
        updateEvidenceList(role);
      }
    };
  } else {
    textArea.style.display = 'none';
  }
}

function updateEvidenceList(role) {
  const listElement = document.getElementById(`${role}-evidence-list`);
  listElement.innerHTML = '';
  evidenceList[role].forEach((evidence, index) => {
    const item = document.createElement('div');
    item.className = 'evidence-item';
    if (evidence.type === 'file') {
      item.innerHTML = `<span>${evidence.name}</span><span class="evidence-item-remove" data-role="${role}" data-index="${index}">删除</span>`;
    } else {
      item.innerHTML = `<span>文字证据: ${evidence.content.substring(0, 30)}${evidence.content.length > 30 ? '...' : ''}</span><span class="evidence-item-remove" data-role="${role}" data-index="${index}">删除</span>`;
    }
    listElement.appendChild(item);
  });
  document.querySelectorAll('.evidence-item-remove').forEach(btn => {
    btn.addEventListener('click', function() {
      const role = this.getAttribute('data-role');
      const index = parseInt(this.getAttribute('data-index'));
      evidenceList[role].splice(index, 1);
      updateEvidenceList(role);
    });
  });
}

// ========== 启动庭审 ==========
async function startTrial() {
  if (!validateTrialForm()) return;
  const caseInfo = collectCaseInfo();
  const payload = {
    case_title: caseInfo.summary,
    plaintiff_name: "原告", // 或 caseInfo.plaintiff.name
    defendant_name: "被告", // 或 caseInfo.defendant.name
    case_type: caseInfo.caseType,
    plaintiff_claim: caseInfo.plaintiff.claim,
    plaintiff_reason: caseInfo.plaintiff.reason,
    defendant_response: caseInfo.defendant.opinion
  };
  await fetch('http://127.0.0.1:8000/court/start_trial', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });
  courtSessionStarted = true;
  document.getElementById('court-prepare').style.display = 'none';
  document.getElementById('court-trial').style.display = 'block';
  document.getElementById('court-chat-history').innerHTML = '';
  await advanceTrial();
  displayCaseInfo(caseInfo);
}

// ========== 推进庭审主流程 ==========
async function advanceTrial(userInput = null) {
  // 用户输入时，举证阶段提交证据
  if (userInput && currentStage === 'evidence_presentation') {
    await submitEvidence(userRole, userInput);
  }
  // 推进流程
  const res = await fetch('http://127.0.0.1:8000/court/advance_trial');
  const result = await res.json();
  currentStage = result.current_stage;
  currentRole = result.current_role;
  updateProgressBar(result.stage_progress);
  // 展示AI输出
  if (result.output) {
    appendCourtMessage(currentRole, result.output);
  }
  // 判断是否需要用户输入
  if (currentRole === getRoleName(userRole) && needUserInput(currentStage)) {
    showInputArea(true);
  } else {
    showInputArea(false);
    // AI自动推进
    setTimeout(() => advanceTrial(), 1200);
  }
}

// ========== 发送用户消息 ==========
async function sendCourtMessage() {
  const input = document.getElementById('court-message-input');
  const text = input.value.trim();
  if (!text) return;
  appendCourtMessage(getRoleName(userRole), text);
  input.value = '';
  await advanceTrial(text);
}

// ========== 证据提交 ==========
async function submitEvidence(role, content) {
  const evidence = {
    name: '证据',
    source: getRoleName(role) + '提交',
    purpose: '证明案件事实',
    content: content
  };
  await fetch('http://127.0.0.1:8000/court/submit_evidence?role=' + role, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(evidence)
  });
}

// ========== 消息展示 ==========
function appendCourtMessage(role, text) {
  const chatHistory = document.getElementById('court-chat-history');
  const messageDiv = document.createElement('div');
  if (role === '法官') {
    messageDiv.className = 'court-message judge';
  } else if (role === '原告') {
    messageDiv.className = 'court-message plaintiff';
  } else if (role === '被告') {
    messageDiv.className = 'court-message defendant';
  } else {
    messageDiv.className = 'court-message';
  }
  messageDiv.textContent = text;
  chatHistory.appendChild(messageDiv);
  chatHistory.scrollTop = chatHistory.scrollHeight;
}

// ========== 工具函数 ==========
function getRoleName(role) {
  if (role === 'plaintiff') return '原告';
  if (role === 'defendant') return '被告';
  if (role === 'judge') return '法官';
  return role;
}
function needUserInput(stage) {
  // 只在原告/被告陈述、举证、质证、辩论等阶段需要用户输入
  return ['plaintiff_statement', 'defendant_defense', 'evidence_presentation', 'evidence_cross_examination', 'court_debate', 'final_statement'].includes(stage);
}
function showInputArea(show) {
  document.querySelector('.court-chat-input').style.display = show ? 'flex' : 'none';
}
function updateProgressBar(progress) {
  const progressBar = document.getElementById('trial-progress-bar');
  if (progressBar) {
    progressBar.style.width = `${progress}%`;
    progressBar.setAttribute('aria-valuenow', progress);
  }
}

// ========== 表单校验、案件信息收集、重置等 ==========
function validateTrialForm() {
  const caseSummary = document.getElementById('case-summary').value.trim();
  if (!caseSummary) {
    alert('请填写案情简述');
    return false;
  }
  const plaintiffClaim = document.getElementById('plaintiff-claim').value.trim();
  const plaintiffReason = document.getElementById('plaintiff-reason').value.trim();
  if (!plaintiffClaim) {
    alert('请填写原告诉讼请求');
    return false;
  }
  if (!plaintiffReason) {
    alert('请填写原告事实和理由');
    return false;
  }
  const defendantOpinion = document.getElementById('defendant-opinion').value.trim();
  const defendantReason = document.getElementById('defendant-reason').value.trim();
  if (!defendantOpinion) {
    alert('请填写被告答辩意见');
    return false;
  }
  if (!defendantReason) {
    alert('请填写被告事实和理由');
    return false;
  }
  return true;
}

function collectCaseInfo() {
  const caseTypeRadio = document.querySelector('input[name="case-type"]:checked');
  const caseTypeText = caseTypeRadio.value === 'other'
    ? document.getElementById('other-case-type').value.trim()
    : caseTypeRadio.nextElementSibling.textContent.trim();
  return {
    role: userRole,
    caseType: caseTypeText,
    summary: document.getElementById('case-summary').value.trim(),
    plaintiff: {
      claim: document.getElementById('plaintiff-claim').value.trim(),
      reason: document.getElementById('plaintiff-reason').value.trim(),
      evidence: evidenceList.plaintiff
    },
    defendant: {
      opinion: document.getElementById('defendant-opinion').value.trim(),
      reason: document.getElementById('defendant-reason').value.trim(),
      evidence: evidenceList.defendant
    }
  };
}

function startNewTrial() {
  // 重置状态
  currentStage = null;
  currentRole = null;
  userRole = 'plaintiff';
  courtSessionStarted = false;
  evidenceList = { plaintiff: [], defendant: [] };
  document.getElementById('case-summary').value = '';
  document.getElementById('plaintiff-claim').value = '';
  document.getElementById('plaintiff-reason').value = '';
  document.getElementById('defendant-opinion').value = '';
  document.getElementById('defendant-reason').value = '';
  document.getElementById('plaintiff-evidence-list').innerHTML = '';
  document.getElementById('defendant-evidence-list').innerHTML = '';
  document.querySelector('input[name="role"][value="plaintiff"]').checked = true;
  document.querySelector('input[name="case-type"][value="loan"]').checked = true;
  document.getElementById('other-case-type').style.display = 'none';
  document.getElementById('court-end').style.display = 'none';
  document.getElementById('court-prepare').style.display = 'block';
  document.getElementById('court-chat-history').innerHTML = '';
  updateEvidenceList('plaintiff');
  updateEvidenceList('defendant');
  updateProgressBar(0);
}

function displayCaseInfo(caseInfo) {
  const infoPanel = document.getElementById('trial-case-info');
  infoPanel.innerHTML = `
    <div class="case-info-item"><strong>案件类型：</strong>${caseInfo.caseType}</div>
    <div class="case-info-item"><strong>案情简述：</strong>${caseInfo.summary}</div>
    <div class="case-info-item"><strong>原告诉讼请求：</strong>${caseInfo.plaintiff.claim}</div>
    <div class="case-info-item"><strong>被告答辩意见：</strong>${caseInfo.defendant.opinion}</div>
  `;
}