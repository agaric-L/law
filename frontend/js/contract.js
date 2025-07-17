// 智能合同功能JS
let contractText = '';

// 智能合同历史记录本地存储
function getContractHistory() {
  return JSON.parse(localStorage.getItem('contract_review_history') || '[]');
}

function saveContractHistory(history) {
  localStorage.setItem('contract_review_history', JSON.stringify(history));
}

function addContractHistory(item) {
  const history = getContractHistory();
  // 添加时间戳
  const historyItem = {
    ...item,
    timestamp: new Date().toLocaleString('zh-CN')
  };
  history.unshift(historyItem);
  if(history.length > 10) history.length = 10; // 最多保存10条
  saveContractHistory(history);
}

// 合同历史记录显示
function renderContractHistory() {
  const historyList = document.getElementById('contractHistoryList');
  if(!historyList) return;
  const history = getContractHistory();
  historyList.innerHTML = '';
  if(history.length === 0) {
    historyList.innerHTML = '<div style="color:#bbb;text-align:center;padding:20px;">暂无历史记录</div>';
    return;
  }
  history.forEach((h, i) => {
    const div = document.createElement('div');
    div.style.background = '#f7f8fa';
    div.style.borderRadius = '6px';
    div.style.padding = '12px 14px';
    div.style.marginBottom = '10px';
    div.style.cursor = 'pointer';
    div.style.border = '1px solid #eee';
    div.innerHTML = `
      <div style='font-size:15px;color:#6f4a8e;font-weight:bold;margin-bottom:4px;'>${h.filename || '合同'}</div>
      <div style='font-size:12px;color:#666;'>${h.timestamp || '未知时间'}</div>
    `;
    div.onclick = () => {
      showContractReviewPopup(h.suggestion);
    };
    historyList.appendChild(div);
  });
}

// 合同审查建议弹出页面控制
function showContractReviewPopup(content) {
  let formatted = '';
  let obj = null;
  // 1. 先处理字符串内容
  if (typeof content === 'string') {
    let str = content.trim();
    // 处理```json代码块
    if (str.startsWith('```json')) {
      str = str.replace(/^```json[\r\n]*/i, '').replace(/```$/, '').trim();
    } else if (str.startsWith('```')) {
      str = str.replace(/^```[\w]*[\r\n]*/i, '').replace(/```$/, '').trim();
    }
    // 尝试解析JSON
    try {
      obj = JSON.parse(str);
    } catch (e) {
      obj = null;
    }
    if (!obj) {
      // 解析失败，原样展示
      document.getElementById('contractReviewContent').innerHTML = content.replace(/\n/g, '<br>');
      document.getElementById('contractReviewPopup').style.display = 'flex';
      return;
    }
  } else if (typeof content === 'object') {
    obj = content;
  }

  // 兼容更多key
  const summaryKeys = ['摘要', 'summary', 'contract_summary', '合同摘要'];
  const riskKeys = ['潜在风险条款', 'risk_clauses', 'risk_warnings', '风险提示', 'risk_tips', 'potential_risks'];

  // 递归美化对象
  function renderObject(val, indent = 1) {
    let html = '';
    if (typeof val === 'string') {
      html += `<div style="margin-left:${indent}em;">${val}</div>`;
    } else if (Array.isArray(val)) {
      val.forEach((item, idx) => {
        if (typeof item === 'object' && item !== null) {
          html += `<div style="margin-left:${indent}em;margin-bottom:4px;"><b>${idx+1}.</b></div>`;
          html += renderObject(item, indent + 1);
        } else {
          html += `<div style="margin-left:${indent}em;">${item}</div>`;
        }
      });
    } else if (typeof val === 'object' && val !== null) {
      for (const k in val) {
        html += `<div style="margin-left:${indent}em;">${k}：${val[k]}</div>`;
      }
    }
    return html;
  }

  // 美化摘要
  function renderSummaryBlock(val) {
    let html = '<div style="font-weight:bold;margin-bottom:8px;">合同摘要</div>';
    html += renderObject(val, 1);
    html += '<br>';
    return html;
  }

  // 美化风险条款
  function renderRiskBlock(val) {
    let html = '<div style="font-weight:bold;margin-bottom:8px;">潜在风险条款</div>';
    if (Array.isArray(val)) {
      val.forEach((item, idx) => {
        if (typeof item === 'object' && item !== null) {
          html += `<div style="margin-left:1em;margin-bottom:4px;"><b>${idx+1}. ${item['风险类型']||item['type']||''}</b></div>`;
          if(item['描述']||item['desc']){
            html += `<div style="margin-left:2.5em;margin-bottom:8px;">${item['描述']||item['desc']}</div>`;
          }
          // 展示其他字段
          for (const k in item) {
            if (k !== '风险类型' && k !== 'type' && k !== '描述' && k !== 'desc') {
              html += `<div style="margin-left:2.5em;">${k}：${typeof item[k]==='object'?renderObject(item[k],3):item[k]}</div>`;
            }
          }
        } else {
          html += `<div style="margin-left:1em;margin-bottom:4px;">${item}</div>`;
        }
      });
    } else {
      html += renderObject(val, 1);
    }
    html += '<br>';
    return html;
  }

  if (obj) {
    // 优先渲染摘要
    for (const key of summaryKeys) {
      if (obj[key]) {
        formatted += renderSummaryBlock(obj[key]);
        break;
      }
    }
    // 优先渲染风险条款
    for (const key of riskKeys) {
      if (obj[key]) {
        formatted += renderRiskBlock(obj[key]);
        break;
      }
    }
    // 渲染其他字段
    for (const k in obj) {
      if (!summaryKeys.includes(k) && !riskKeys.includes(k)) {
        formatted += `<div style="font-weight:bold;margin-top:12px;">${k}</div>`;
        formatted += renderObject(obj[k], 1);
      }
    }
  }
  document.getElementById('contractReviewContent').innerHTML = formatted;
  document.getElementById('contractReviewPopup').style.display = 'flex';
}

function closeContractReviewPopup() {
  document.getElementById('contractReviewPopup').style.display = 'none';
}

function handleFile(file) {
  const uploadText = document.getElementById('uploadText');
  const reviewBtn = document.getElementById('reviewBtn');
  
  // 检查文件类型
  const allowedTypes = ['text/plain', 'application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'];
  const allowedExtensions = ['.txt', '.pdf', '.docx'];
  
  const isValidType = allowedTypes.includes(file.type) || 
                     allowedExtensions.some(ext => file.name.toLowerCase().endsWith(ext));
  
  if(isValidType) {
    uploadText.innerText = '已上传：' + file.name;
    reviewBtn.disabled = false;
  } else {
    uploadText.innerText = '仅支持 .txt/.docx/.pdf 文件';
    reviewBtn.disabled = true;
  }
}

<<<<<<< HEAD
function disableBodyScroll() {
  document.body.style.overflow = 'hidden';
}
function enableBodyScroll() {
  document.body.style.overflow = '';
}

// 监听页面切换，只有在显示智能合同页面时禁止滚动
function observeContractPage() {
  const contractPage = document.getElementById('page-contract');
  const observer = new MutationObserver(() => {
    if (contractPage && contractPage.style.display !== 'none') {
      disableBodyScroll();
    } else {
      enableBodyScroll();
    }
  });
  observer.observe(contractPage, { attributes: true, attributeFilter: ['style'] });
}

// 当进入智能合同页面时调用
// disableBodyScroll(); // 移除此行，改为监听页面显示

// 当离开智能合同页面时调用
// enableBodyScroll(); // 移除此行，改为监听页面显示

=======
>>>>>>> e5db59705d7ac3e53137f9b5db64196b88c254fa
// 初始化智能合同功能
function initContract() {
  const fileInput = document.getElementById('contractFile');
  const reviewBtn = document.getElementById('reviewBtn');
  const uploadBox = document.getElementById('uploadBox');
  const uploadText = document.getElementById('uploadText');

  if(fileInput && reviewBtn && uploadBox) {
    // 文件上传事件
    uploadBox.addEventListener('click', () => fileInput.click());
    
    // 拖拽事件
    uploadBox.addEventListener('dragover', e => { 
      e.preventDefault(); 
      uploadBox.style.borderColor = '#4f7cff'; 
    });
    
    uploadBox.addEventListener('dragleave', e => { 
      e.preventDefault(); 
      uploadBox.style.borderColor = '#a0a0ff'; 
    });
    
    uploadBox.addEventListener('drop', async e => {
      e.preventDefault();
      uploadBox.style.borderColor = '#a0a0ff';
      if(e.dataTransfer.files.length) {
        fileInput.files = e.dataTransfer.files;
        handleFile(fileInput.files[0]);
      }
    });
    
    // 文件选择事件
    fileInput.addEventListener('change', e => {
      if(e.target.files[0]) handleFile(e.target.files[0]);
    });
    
    // 审查按钮事件
    reviewBtn.addEventListener('click', async () => {
      if (!fileInput.files[0]) {
        alert('请先上传合同文件');
        return;
      }
<<<<<<< HEAD
      // 显示加载中
      reviewBtn.disabled = true;
      const oldText = reviewBtn.textContent;
      reviewBtn.textContent = '加载中...';
      try {
            const formData = new FormData();
            formData.append('file', fileInput.files[0]);

            const res = await fetch('http://127.0.0.1:8000/smart_contracts/analyze_contract/', {
              method: 'POST',
              body: formData
            });
            
            if (!res.ok) {
              throw new Error(`HTTP error! status: ${res.status}`);
            }
            
            const data = await res.json();
            const analysis = data.analysis || {};
            const suggestion = analysis.raw || JSON.stringify(analysis, null, 2);

=======
      
      try {
        const formData = new FormData();
        formData.append('file', fileInput.files[0]);
        
        const res = await fetch('http://localhost:8000/smart_contracts/analyze_contract/', {
          method: 'POST',
          body: formData
        });
        
        if (!res.ok) {
          throw new Error(`HTTP error! status: ${res.status}`);
        }
        
        const data = await res.json();
        const analysis = data.analysis || {};
        const suggestion = analysis.raw || JSON.stringify(analysis, null, 2);
        
>>>>>>> e5db59705d7ac3e53137f9b5db64196b88c254fa
        // 保存历史
        addContractHistory({
          filename: uploadText.innerText.replace('已上传：',''), 
          suggestion: suggestion
        });
        renderContractHistory();
        
        // 显示弹出页面
        showContractReviewPopup(suggestion);
      } catch (error) {
        console.error('分析失败:', error);
        const errorMsg = '服务器暂时无法响应，请稍后重试。';
        alert(errorMsg);
<<<<<<< HEAD
      } finally {
        // 恢复按钮状态
        reviewBtn.disabled = false;
        reviewBtn.textContent = oldText;
=======
>>>>>>> e5db59705d7ac3e53137f9b5db64196b88c254fa
      }
    });
    
    // 初始化历史
    renderContractHistory();
    
    // 绑定弹出页面点击外部关闭事件
    document.getElementById('contractReviewPopup').addEventListener('click', function(e) {
      if (e.target === this) {
        closeContractReviewPopup();
      }
    });
  }
}

// 页面加载完成后初始化智能合同功能
document.addEventListener('DOMContentLoaded', function() {
  initContract();
<<<<<<< HEAD
  observeContractPage(); // 在DOMContentLoaded中调用监听函数
});
=======
}); 
>>>>>>> e5db59705d7ac3e53137f9b5db64196b88c254fa
