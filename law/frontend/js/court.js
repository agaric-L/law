// ========== 全局变量与初始化 ==========
let currentStage = null;
let currentRole = null;
let userRole = 'plaintiff'; // 用户选择的角色
let courtSessionStarted = false;
let currentSessionId = null; // 当前会话ID
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
  
  // 案件类型选择
  document.querySelectorAll('input[name="case-type"]').forEach(radio => {
    radio.addEventListener('change', function() {
      const otherInput = document.getElementById('other-case-type');
      if (this.value === 'other') {
        otherInput.style.display = 'block';
      } else {
        otherInput.style.display = 'none';
      }
    });
  });
  
  // 证据上传按钮事件
  const plaintiffEvidenceFile = document.getElementById('plaintiff-evidence-file');
  const defendantEvidenceFile = document.getElementById('defendant-evidence-file');
  
  if (plaintiffEvidenceFile) {
    plaintiffEvidenceFile.addEventListener('change', function(e) {
      handleFileUpload(e, 'plaintiff');
    });
  }
  
  if (defendantEvidenceFile) {
    defendantEvidenceFile.addEventListener('change', function(e) {
      handleFileUpload(e, 'defendant');
    });
  }
  
  // 文字证据按钮事件
  const plaintiffEvidenceTextBtn = document.getElementById('plaintiff-evidence-text-btn');
  const defendantEvidenceTextBtn = document.getElementById('defendant-evidence-text-btn');
  
  if (plaintiffEvidenceTextBtn) {
    plaintiffEvidenceTextBtn.addEventListener('click', function() {
      toggleTextEvidence('plaintiff');
    });
  }
  
  if (defendantEvidenceTextBtn) {
    defendantEvidenceTextBtn.addEventListener('click', function() {
      toggleTextEvidence('defendant');
    });
  }
  // 开始庭审
  const startTrialBtn = document.getElementById('start-trial-btn');
  if (startTrialBtn) {
    startTrialBtn.addEventListener('click', startTrial);
  }
  
  // 发送消息
  const sendCourtMessageBtn = document.getElementById('send-court-message-btn');
  if (sendCourtMessageBtn) {
    sendCourtMessageBtn.addEventListener('click', sendCourtMessage);
  }
  
  // 新庭审
  const newTrialBtn = document.getElementById('new-trial-btn');
  if (newTrialBtn) {
    newTrialBtn.addEventListener('click', startNewTrial);
  }
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
  console.log('开始庭审按钮被点击');
  
  if (!validateTrialForm()) {
    console.log('表单验证失败');
    return;
  }
  
  console.log('表单验证通过，开始收集案件信息');
  const caseInfo = collectCaseInfo();
  console.log('案件信息:', caseInfo);
  
  const payload = {
    case_title: caseInfo.summary,
    plaintiff_name: "原告",
    defendant_name: "被告",
    case_type: caseInfo.caseType,
    plaintiff_claim: caseInfo.plaintiff.claim,
    plaintiff_reason: caseInfo.plaintiff.reason,
    defendant_response: caseInfo.defendant.opinion,
    defendant_reason: caseInfo.defendant.reason,
    user_role: userRole
  };
  
  console.log('发送到后端的payload:', payload);
  
  try {
    console.log('正在发送请求到后端...');
    const response = await fetch('http://127.0.0.1:8000/court/start_trial', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    
    console.log('后端响应状态:', response.status);
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const result = await response.json();
    console.log('后端返回结果:', result);
    
    currentSessionId = result.session_id;
    courtSessionStarted = true;
    
    console.log('切换到庭审页面');
    // 切换到庭审页面
    document.getElementById('court-prepare').style.display = 'none';
    document.getElementById('court-trial').style.display = 'block';
    document.getElementById('court-chat-history').innerHTML = '';
    
    // 更新进度条状态 - 进入开庭审理阶段
    updateProgressBar('trial');
    
    // 开始庭审流程
    console.log('开始推进庭审流程');
    await advanceTrial();
    displayCaseInfo(caseInfo);
    
  } catch (error) {
    console.error('启动庭审失败:', error);
    alert('启动庭审失败，请重试。错误信息：' + error.message);
  }
}




// ========== 推进庭审主流程 ==========
async function advanceTrial(userInput = null) {
  if (!currentSessionId) {
    console.error('没有有效的会话ID');
    return;
  }
  
  try {
    const payload = {
      session_id: currentSessionId,
      user_input: userInput || ""
    };
    
    const response = await fetch('http://127.0.0.1:8000/court/advance_trial', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    
    const result = await response.json();
    currentStage = result.phase;
    currentRole = result.current_role;
    
    // 展示AI输出
    if (result.content && result.content.length > 0) {
      for (const content of result.content) {
        // 检查是否为新的数据结构（包含role字段）
        if (typeof content === 'object' && content.role && content.content) {
          // 新的数据结构，直接使用role字段
          appendCourtMessage(content.role, content.content);
        } else {
          // 旧的数据结构，使用内容判断角色
          let speaker = '法官';
          
          // 优先判断是否为法官发言（法官的发言通常包含特定词汇）
          if (content.includes('现在开庭') || content.includes('请') || content.includes('本院') || 
              content.includes('法院') || content.includes('法庭') || content.includes('审判长') || 
              content.includes('法官') || content.includes('全体起立') || content.includes('请坐') ||
              content.includes('现在开始') || content.includes('请陈述') || content.includes('请出示') ||
              content.includes('请回答') || content.includes('请质证') || content.includes('请辩论') ||
              content.includes('合议庭') || content.includes('书记员') || content.includes('当事人') ||
              content.includes('现在审理') || content.includes('本案') || content.includes('现在进行')) {
            speaker = '法官';
          }
          // 然后判断是否为原告发言
          else if (content.includes('原告') && (content.includes('起诉') || content.includes('诉讼请求') || 
                   content.includes('出示证据') || content.includes('陈述') || content.includes('原告起诉状') ||
                   content.includes('原告认为') || content.includes('原告主张'))) {
            speaker = '原告';
          }
          // 最后判断是否为被告发言
          else if (content.includes('被告') && (content.includes('答辩') || content.includes('质证') || 
                   content.includes('回答') || content.includes('辩论') || content.includes('最后陈述') ||
                   content.includes('被告答辩意见') || content.includes('被告认为') || content.includes('被告主张'))) {
            speaker = '被告';
          }
          appendCourtMessage(speaker, content);
        }
      }
    }
    
    // 判断是否需要用户输入
    if (result.need_user_input) {
      showInputArea(true);
      // 显示当前角色提示
      const inputArea = document.querySelector('.court-chat-input');
      const roleHint = document.createElement('div');
      roleHint.className = 'role-hint';
      
       // 根据用户选择的角色显示相应的提示
       let hintText = '';
       if (userRole === 'plaintiff' && result.current_role === '原告') {
         hintText = '当前轮到原告发言';
       } else if (userRole === 'defendant' && result.current_role === '被告') {
         hintText = '当前轮到被告发言';
       } else {
         hintText = `当前轮到${result.current_role}发言`;
       }
      
      roleHint.textContent = hintText;
      roleHint.style.cssText = 'color: #4f7cff; font-weight: bold; margin-bottom: 10px; text-align: center; padding: 10px; background: #f0f8ff; border-radius: 8px;';
      inputArea.insertBefore(roleHint, inputArea.firstChild);
      
      // 为输入框添加占位符提示
      const messageInput = document.getElementById('court-message-input');
      if (messageInput) {
        messageInput.placeholder = '输入您的发言';
      }
    } else {
      showInputArea(false);
      // 如果不需要用户输入且庭审未结束，继续自动推进
      if (!result.trial_completed) {
        setTimeout(() => advanceTrial(), 2000);
      } else {
        // 庭审结束，显示判决结果
        showJudgment();
      }
    }
    
  } catch (error) {
    console.error('推进庭审失败:', error);
    alert('推进庭审失败，请重试');
  }
}

// ========== 发送用户消息 ==========
async function sendCourtMessage() {
  const input = document.getElementById('court-message-input');
  const text = input.value.trim();
  if (!text) return;
  
  // 显示用户消息
  appendCourtMessage(getRoleName(userRole), text);
  input.value = '';
  
  // 移除角色提示
  const roleHint = document.querySelector('.role-hint');
  if (roleHint) {
    roleHint.remove();
  }
  
  // 推进庭审
  await advanceTrial(text);
}

// ========== 快速填充示例内容 ==========
function fillExampleContent() {
  const input = document.getElementById('court-message-input');
  const currentPhase = currentStage;
  
  let exampleText = '';
  
  if (currentPhase === '原告陈述') {
    exampleText = `原告起诉状：
原告与被告于2023年1月1日签订借款协议，原告向被告出借10万元，约定年利率4%，借款期限为一年。原告已按约定履行出借义务，但被告至今未按约定归还借款本金及利息。现请求法院判令被告归还借款本金10万元及利息。`;
  } else if (currentPhase === '被告答辩') {
    exampleText = `被告答辩意见：
不同意原告诉讼请求，请求法院驳回。被告已于2023年6月通过银行转账归还全部借款，原告所述借款事实不属实，被告未收到相关款项。`;
  } else if (currentPhase === '举证') {
    exampleText = `原告出示证据：
1. 借款协议书 - 来源于原告与被告签订的书面协议，用于证明借款事实和约定内容；
2. 银行转账凭证 - 来源于银行出具的转账记录，用于证明原告已履行出借义务。`;
  } else if (currentPhase === '质证') {
    exampleText = `被告质证意见：
对于原告出示的借款协议书，被告认为该协议系伪造，被告从未与原告签订过任何借款协议。对于银行转账凭证，被告认为该转账记录与本案无关。`;
  } else if (currentPhase === '法庭询问') {
    exampleText = `被告回答：
被告确实没有收到原告所称的10万元借款，被告的银行流水可以证明没有相关收款记录。`;
  } else if (currentPhase === '法庭辩论') {
    exampleText = `被告辩论意见：
原告无法提供真实的借款协议和有效的转账凭证，其诉讼请求缺乏事实和法律依据，请求法院驳回原告的全部诉讼请求。`;
  } else if (currentPhase === '最后陈述') {
    exampleText = `被告最后陈述：
请求法院驳回原告的诉讼请求，维护被告的合法权益。`;
  }
  
  if (exampleText) {
    input.value = exampleText;
    input.focus();
  }
}

// ========== 证据提交 ==========
async function submitEvidence(role, content) {
  if (!currentSessionId) return;
  
  const evidence = {
    name: '证据',
    source: getRoleName(role) + '提交',
    purpose: '证明案件事实',
    content: content
  };
  
  try {
    await fetch(`http://127.0.0.1:8000/court/submit_evidence?role=${role}&session_id=${currentSessionId}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(evidence)
    });
  } catch (error) {
    console.error('提交证据失败:', error);
  }
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
  
  // 添加角色标签
  const roleLabel = document.createElement('div');
  roleLabel.className = 'message-role-label';
  roleLabel.textContent = role;
  roleLabel.style.cssText = `
    font-size: 12px;
    color: #666;
    margin-bottom: 4px;
    font-weight: bold;
  `;
  
  // 为不同角色设置不同的标签样式
  if (role === '原告') {
    roleLabel.style.textAlign = 'right';
    roleLabel.style.color = '#4f7cff';
  } else if (role === '被告') {
    roleLabel.style.textAlign = 'left';
    roleLabel.style.color = '#666';
  } else if (role === '法官') {
    roleLabel.style.textAlign = 'center';
    roleLabel.style.color = '#4f7cff';
  }
  
  const messageWrapper = document.createElement('div');
  messageWrapper.style.cssText = `
    margin-bottom: 15px;
    max-width: 80%;
    ${role === '原告' ? 'margin-left: auto;' : ''}
    ${role === '被告' ? 'margin-right: auto;' : ''}
    ${role === '法官' ? 'margin: 15px auto;' : ''}
  `;
  
  messageWrapper.appendChild(roleLabel);
  messageDiv.textContent = text;
  messageWrapper.appendChild(messageDiv);
  chatHistory.appendChild(messageWrapper);
  chatHistory.scrollTop = chatHistory.scrollHeight;
}

// ========== 显示判决结果 ==========
function showJudgment() {
  // 切换到判决页面
  document.getElementById('court-trial').style.display = 'none';
  document.getElementById('court-end').style.display = 'block';
  
  // 更新进度条状态 - 进入庭审结束阶段
  updateProgressBar('end');
  
  // 获取判决内容（这里可以从会话中获取）
  const judgmentContent = document.getElementById('judgment-content');
  judgmentContent.innerHTML = `
    <h3>判决书</h3>
    <p>根据《中华人民共和国民事诉讼法》相关规定，经过审理查明：</p>
    <p>原告诉称：请求判令被告偿还借款本金10万元及利息。</p>
    <p>被告辩称：不同意偿还，借款已经归还。</p>
    <p>本院认为，根据双方陈述和证据，依法判决如下：</p>
    <p>......</p>
    <p>如不服本判决，可在收到判决书之日起15日内上诉。</p>
  `;
}

// ========== 工具函数 ==========
function updateProgressBar(stage) {
  // 移除所有步骤的active状态
  document.querySelectorAll('.process-step').forEach(step => {
    step.classList.remove('active');
  });
  
  // 根据阶段设置对应的active状态
  switch(stage) {
    case 'prepare':
      document.getElementById('step-prepare').classList.add('active');
      break;
    case 'trial':
      document.getElementById('step-trial').classList.add('active');
      break;
    case 'end':
      document.getElementById('step-end').classList.add('active');
      break;
  }
}

function getRoleName(role) {
  if (role === 'plaintiff') return '原告';
  if (role === 'defendant') return '被告';
  if (role === 'judge') return '法官';
  return role;
}

function showInputArea(show) {
  const inputArea = document.querySelector('.court-chat-input');
  if (inputArea) {
    inputArea.style.display = show ? 'flex' : 'none';
  }
}

// ========== 表单校验、案件信息收集、重置等 ==========
function validateTrialForm() {
  console.log('开始表单验证');
  
  const caseSummary = document.getElementById('case-summary').value.trim();
  console.log('案情简述:', caseSummary);
  if (!caseSummary) {
    alert('请填写案情简述');
    return false;
  }
  
  const plaintiffClaim = document.getElementById('plaintiff-claim').value.trim();
  const plaintiffReason = document.getElementById('plaintiff-reason').value.trim();
  console.log('原告诉讼请求:', plaintiffClaim);
  console.log('原告事实和理由:', plaintiffReason);
  
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
  console.log('被告答辩意见:', defendantOpinion);
  console.log('被告事实和理由:', defendantReason);
  
  if (!defendantOpinion) {
    alert('请填写被告答辩意见');
    return false;
  }
  if (!defendantReason) {
    alert('请填写被告事实和理由');
    return false;
  }
  
  console.log('表单验证通过');
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
  currentSessionId = null;
  evidenceList = { plaintiff: [], defendant: [] };
  
  // 重置表单
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
  
  // 切换页面
  document.getElementById('court-end').style.display = 'none';
  document.getElementById('court-prepare').style.display = 'block';
  document.getElementById('court-chat-history').innerHTML = '';
  
  // 重置进度条状态 - 回到开庭前准备阶段
  updateProgressBar('prepare');
  
  // 更新证据列表
  updateEvidenceList('plaintiff');
  updateEvidenceList('defendant');
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