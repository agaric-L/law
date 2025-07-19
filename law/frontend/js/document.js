// 文书生成功能JS
let currentDocType = '民事起诉状'; // 默认文书类型
let documentHistory = []; // 文书生成历史记录
let hasUserInput = false; // 跟踪用户是否已输入内容

// 文书生成历史记录本地存储
function getDocumentHistory() {
  return JSON.parse(localStorage.getItem('document_generation_history') || '[]');
}

function saveDocumentHistory(history) {
  localStorage.setItem('document_generation_history', JSON.stringify(history));
}

function addDocumentHistory(item) {
  const history = getDocumentHistory();
  // 添加时间戳
  const historyItem = {
    ...item,
    timestamp: new Date().toLocaleString('zh-CN')
  };
  history.unshift(historyItem);
  if(history.length > 10) history.length = 10; // 最多保存10条
  saveDocumentHistory(history);
}

// 文书历史记录显示
function renderDocumentHistory() {
  const historyList = document.getElementById('documentHistoryList');
  if(!historyList) return;
  const history = getDocumentHistory();
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
      <div style='font-size:15px;color:#6f4a8e;font-weight:bold;margin-bottom:4px;'>${h.docType || '文书'}</div>
      <div style='font-size:12px;color:#666;'>${h.timestamp || '未知时间'}</div>
    `;
    div.onclick = () => {
      showDocumentPopup(h.content, h.docType);
    };
    historyList.appendChild(div);
  });
}

// 文书生成弹出页面控制
function showDocumentPopup(content, docType) {
  const popup = document.getElementById('documentPopup');
  const contentDiv = document.getElementById('documentContent');
  const titleDiv = document.getElementById('documentTitle');
  const saveBtn = document.getElementById('savePdfBtn');
  
  if(popup && contentDiv && titleDiv) {
    titleDiv.textContent = docType || '法律文书';
    // 保持原始格式，使用pre-wrap样式
    contentDiv.innerHTML = content.replace(/\n/g, '<br>');
    contentDiv.style.whiteSpace = 'pre-wrap';
    contentDiv.style.wordWrap = 'break-word';
    contentDiv.style.lineHeight = '1.8';
    contentDiv.style.fontFamily = 'SimSun, 宋体, serif';
    contentDiv.style.fontSize = '14px';
    
    popup.style.display = 'flex';
    
    // 重置用户输入状态
    hasUserInput = false;
    
    // 绑定保存PDF事件 - 确保每次打开弹窗都重新绑定
    if (saveBtn) {
      saveBtn.onclick = async function() {
        try {
          // 检查html2pdf是否可用
          if (typeof html2pdf === 'undefined') {
            alert('PDF生成库未加载，请刷新页面重试');
            return;
          }

          const element = document.getElementById('documentContent');
          if (!element) {
            alert('找不到文档内容');
            return;
          }

          // 显示加载提示
          const originalText = saveBtn.textContent;
          saveBtn.textContent = '正在生成PDF...';
          saveBtn.disabled = true;

          // 获取文档内容
          const content = element.innerText || element.textContent || '';
          
          if (!content.trim()) {
            alert('文档内容为空，无法生成PDF');
            return;
          }

          // 创建PDF容器
          const pdfContainer = document.createElement('div');
          pdfContainer.style.cssText = `
            padding: 20px;
            font-family: 'SimSun', '宋体', serif;
            font-size: 14px;
            line-height: 1.8;
            color: #000;
            background: white;
            width: 210mm;
            min-height: 297mm;
            margin: 0;
            white-space: pre-wrap;
            word-wrap: break-word;
            overflow: visible;
            position: absolute;
            left: -9999px;
            top: -9999px;
          `;
          pdfContainer.innerHTML = content.replace(/\n/g, '<br>');

          // 添加到body中
          document.body.appendChild(pdfContainer);

          // PDF配置
          const opt = {
            margin: [15, 15, 15, 15],
            filename: '法律文书.pdf',
            image: { type: 'jpeg', quality: 0.98 },
            html2canvas: { 
              scale: 2,
              useCORS: true,
              allowTaint: true,
              backgroundColor: '#ffffff'
            },
            jsPDF: { 
              unit: 'mm', 
              format: 'a4', 
              orientation: 'portrait'
            }
          };

          // 生成PDF
          await html2pdf().set(opt).from(pdfContainer).save();
          alert('PDF生成成功！');

        } catch (e) {
          console.error('PDF生成失败:', e);
          alert('PDF生成失败，请重试。错误信息：' + e.message);
        } finally {
          // 恢复按钮状态
          saveBtn.textContent = originalText;
          saveBtn.disabled = false;
          
          // 清理临时元素
          const pdfContainer = document.querySelector('div[style*="210mm"]');
          if (pdfContainer && document.body.contains(pdfContainer)) {
            document.body.removeChild(pdfContainer);
          }
        }
      };
    }
    
    // 添加点击事件监听器，根据用户输入状态决定光标位置
    contentDiv.addEventListener('click', function(e) {
      // 延迟设置光标位置，确保在点击事件处理完成后执行
      setTimeout(() => {
        try {
          const selection = window.getSelection();
          selection.removeAllRanges();
          
          const range = document.createRange();
          
          if (hasUserInput) {
            // 如果用户已输入内容，光标在末尾
            range.setStart(contentDiv, contentDiv.childNodes.length);
            contentDiv.scrollTop = contentDiv.scrollHeight;
          } else {
            // 如果用户未输入内容，光标在开头
            range.setStart(contentDiv, 0);
            contentDiv.scrollTop = 0;
          }
          
          range.collapse(true);
          selection.addRange(range);
        } catch (e) {
          console.log('点击时设置光标位置失败:', e);
        }
      }, 10);
    }, { once: true }); // 只绑定一次，避免重复绑定
    
    // 添加焦点事件监听器，根据用户输入状态决定光标位置
    contentDiv.addEventListener('focus', function(e) {
      // 延迟设置光标位置
      setTimeout(() => {
        try {
          const selection = window.getSelection();
          selection.removeAllRanges();
          
          const range = document.createRange();
          
          if (hasUserInput) {
            // 如果用户已输入内容，光标在末尾
            range.setStart(contentDiv, contentDiv.childNodes.length);
            contentDiv.scrollTop = contentDiv.scrollHeight;
          } else {
            // 如果用户未输入内容，光标在开头
            range.setStart(contentDiv, 0);
            contentDiv.scrollTop = 0;
          }
          
          range.collapse(true);
          selection.addRange(range);
        } catch (e) {
          console.log('聚焦时设置光标位置失败:', e);
        }
      }, 10);
    }, { once: true }); // 只绑定一次，避免重复绑定
    
    // 添加输入事件监听器，当用户输入内容时光标保持在末尾
    contentDiv.addEventListener('input', function(e) {
      // 标记用户已输入内容
      hasUserInput = true;
      
      // 用户输入内容后，光标保持在末尾
      setTimeout(() => {
        try {
          const selection = window.getSelection();
          selection.removeAllRanges();
          
          const range = document.createRange();
          // 设置光标到内容末尾
          range.setStart(contentDiv, contentDiv.childNodes.length);
          range.collapse(true);
          selection.addRange(range);
          
          // 滚动到底部确保光标可见
          contentDiv.scrollTop = contentDiv.scrollHeight;
        } catch (e) {
          console.log('输入时光标设置失败:', e);
        }
      }, 10);
    }, { once: true }); // 只绑定一次，避免重复绑定
  }
}

function closeDocumentPopup() {
  const popup = document.getElementById('documentPopup');
  const contentDiv = document.getElementById('documentContent');
  
  if(popup) {
    popup.style.display = 'none';
    
    // 重置用户输入状态
    hasUserInput = false;
    
    // 清除选择，避免光标残留
    setTimeout(() => {
      window.getSelection().removeAllRanges();
      
      // 移除之前添加的事件监听器，确保下次打开时重新绑定
      if (contentDiv) {
        // 移除所有事件监听器（通过克隆节点的方式）
        const newContentDiv = contentDiv.cloneNode(true);
        contentDiv.parentNode.replaceChild(newContentDiv, contentDiv);
        newContentDiv.id = 'documentContent';
        newContentDiv.contentEditable = 'true';
      }
    }, 50);
  }
}

// 解析用户输入的文本，提取关键信息
function parseUserInput(text) {
  // 检查文本中是否包含特定信息的函数
  function hasInfo(text, keywords) {
    return keywords.some(keyword => text.includes(keyword));
  }
  
  // 检查是否包含日期信息
  function hasDateInfo(text) {
    const datePatterns = [
      /(\d{4}年\d{1,2}月\d{1,2}日)/,
      /(\d{4}-\d{1,2}-\d{1,2})/,
      /(\d{4}\/\d{1,2}\/\d{1,2})/,
      /(出生日期|出生时间|生日)/,
      /(案发时间|事发时间|发生时间)/,
      /(借款时间|借钱时间|借条时间)/,
      /(还款时间|还钱时间)/,
      /(签订时间|签署时间|合同时间)/
    ];
    return datePatterns.some(pattern => pattern.test(text));
  }
  
  // 检查是否包含具体的时间信息（用于在案件事实中标记时间）
  function hasSpecificTimeInfo(text) {
    const timeKeywords = [
      '出生日期', '出生时间', '生日', '案发时间', '事发时间', '发生时间',
      '借款时间', '借钱时间', '借条时间', '还款时间', '还钱时间',
      '签订时间', '签署时间', '合同时间', '违约时间', '到期时间'
    ];
    return timeKeywords.some(keyword => text.includes(keyword));
  }
  
  // 检查是否包含地址信息
  function hasAddressInfo(text) {
    const addressKeywords = [
      '地址', '住址', '居住', '户籍', '户口', '住所', '现住', '现居',
      '省', '市', '县', '区', '街道', '路', '号', '室', '楼', '单元'
    ];
    return hasInfo(text, addressKeywords);
  }
  
  // 检查是否包含联系方式
  function hasContactInfo(text) {
    const contactPatterns = [
      /(\d{11})/, // 手机号
      /(\d{3,4}-\d{7,8})/, // 座机号
      /(电话|手机|联系方式|联系电话|联系手机)/
    ];
    return contactPatterns.some(pattern => pattern.test(text));
  }
  
  // 检查是否包含身份证号
  function hasIdNumber(text) {
    const idPattern = /(\d{17}[\dXx])/;
    return idPattern.test(text) || text.includes('身份证号') || text.includes('身份证号码');
  }
  
  const info = {
    plaintiff: {
      name: '',
      id_type: '身份证',
      id_number: '',
      address: '',
      contact: ''
    },
    defendant: {
      name: '',
      id_type: '身份证', 
      id_number: '',
      address: '',
      contact: ''
    },
    case_info: {
      case_type: '', // 默认不指定类型
      facts: text,
      legal_basis: ''
    },
    claims: [],
    court: 'XX人民法院'
  };
  
  // 尝试从文本中提取原告和被告信息
  const lines = text.split('\n');
  for(let line of lines) {
    line = line.trim();
    if(line.includes('原告') || line.includes('我') || line.includes('本人')) {
      // 提取原告信息
      if(line.includes('姓名') || line.includes('叫')) {
        const nameMatch = line.match(/[姓名叫]([^\s，。]+)/);
        if(nameMatch) info.plaintiff.name = nameMatch[1];
      }
    }
    if(line.includes('被告') || line.includes('对方') || line.includes('他')) {
      // 提取被告信息
      if(line.includes('姓名') || line.includes('叫')) {
        const nameMatch = line.match(/[姓名叫]([^\s，。]+)/);
        if(nameMatch) info.defendant.name = nameMatch[1];
      }
    }
  }
  
  // 如果没有提取到姓名，使用默认值
  if(!info.plaintiff.name) info.plaintiff.name = '原告';
  if(!info.defendant.name) info.defendant.name = '被告';
  
  // 检查并设置缺失信息为XXX
  if(!hasIdNumber(text)) {
    info.plaintiff.id_number = 'XXX';
    info.defendant.id_number = 'XXX';
  }
  
  if(!hasAddressInfo(text)) {
    info.plaintiff.address = 'XXX';
    info.defendant.address = 'XXX';
  }
  
  if(!hasContactInfo(text)) {
    info.plaintiff.contact = 'XXX';
    info.defendant.contact = 'XXX';
  }
  
  // 处理案件事实中的时间信息
  if(!hasSpecificTimeInfo(text)) {
    // 如果用户没有提到具体时间，在案件事实中添加时间占位符
    info.case_info.facts = text + '\n\n注：案发时间、出生日期等具体时间信息用XXX表示。';
  }
  
  // 根据案件类型生成诉讼请求
    info.claims = [
      '判令被告承担相应法律责任',
      '判令被告承担本案诉讼费用'
    ];
  
  return info;
}

// 生成文书
async function generateDocument(docType) {
  const textarea = document.getElementById('docTextarea');
  if(!textarea) {
    alert('找不到输入框');
    return;
  }
  const userInput = textarea.value.trim();
  if(!userInput) {
    alert('请先输入案件描述');
    return;
  }
  try {
    const generateBtn = docType === '民事起诉状' ? document.getElementById('lawsuitBtn') : document.getElementById('defenseBtn');
    if(generateBtn) {
      generateBtn.textContent = '生成中...';
      generateBtn.disabled = true;
    }
    const parsedInfo = parseUserInput(userInput);
    // 流式接口
    const endpoint = docType === '民事起诉状' ? '/generate_lawsuit/stream' : '/generate_defense/stream';
    const response = await fetch(`http://localhost:8000${endpoint}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(parsedInfo)
    });
    // 流式读取
    const popup = document.getElementById('documentPopup');
    const contentDiv = document.getElementById('documentContent');
    let content = '';
    if(popup && contentDiv) {
      popup.style.display = 'flex';
      contentDiv.innerHTML = '';
      contentDiv.style.whiteSpace = 'pre-wrap';
      contentDiv.style.wordWrap = 'break-word';
      contentDiv.style.lineHeight = '1.8';
      contentDiv.style.fontFamily = 'SimSun, 宋体, serif';
      contentDiv.style.fontSize = '14px';
    }
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      const text = decoder.decode(value, { stream: true });
      content += text;
      if(contentDiv) contentDiv.innerHTML = content.replace(/\n/g, '<br>');
    }
    
    // 调用showDocumentPopup来正确显示弹窗并绑定PDF保存事件
    showDocumentPopup(content, docType);
    
    // 保存历史
    addDocumentHistory({
      docType: docType,
      content: content,
      userInput: userInput
    });
    renderDocumentHistory();
  } catch(error) {
    console.error('生成文书失败:', error);
    alert('生成文书失败，请稍后重试。错误信息：' + error.message);
  } finally {
    const generateBtn = docType === '民事起诉状' ? document.getElementById('lawsuitBtn') : document.getElementById('defenseBtn');
    if(generateBtn) {
      generateBtn.textContent = docType;
      generateBtn.disabled = false;
    }
  }
}

// 选项按钮切换与placeholder动态切换
function updateDocTypeUI(selectedType) {
  const lawsuitBtn = document.getElementById('lawsuitBtn');
  const defenseBtn = document.getElementById('defenseBtn');
  const textarea = document.getElementById('docTextarea');
  if (selectedType === '民事起诉状') {
    lawsuitBtn.classList.add('selected');
    lawsuitBtn.style.background = '#4f7cff';
    lawsuitBtn.style.color = '#fff';
    lawsuitBtn.style.border = 'none';
    defenseBtn.classList.remove('selected');
    defenseBtn.style.background = '#fff';
    defenseBtn.style.color = '#4f7cff';
    defenseBtn.style.border = '2px solid #4f7cff';
    textarea.placeholder = '请简要描述您的案件事实、诉讼请求等信息……';
  } else {
    defenseBtn.classList.add('selected');
    defenseBtn.style.background = '#4f7cff';
    defenseBtn.style.color = '#fff';
    defenseBtn.style.border = 'none';
    lawsuitBtn.classList.remove('selected');
    lawsuitBtn.style.background = '#fff';
    lawsuitBtn.style.color = '#4f7cff';
    lawsuitBtn.style.border = '2px solid #4f7cff';
    textarea.placeholder = '请简要描述您对起诉内容的答辩理由、事实等信息……';
  }
  window.currentDocType = selectedType;
}

function initDocument() {
  // 绑定类型按钮
  const lawsuitBtn = document.getElementById('lawsuitBtn');
  const defenseBtn = document.getElementById('defenseBtn');
  if (lawsuitBtn && defenseBtn) {
    lawsuitBtn.onclick = () => updateDocTypeUI('民事起诉状');
    defenseBtn.onclick = () => updateDocTypeUI('民事答辩状');
  }
  // 绑定生成按钮
  const generateBtn = document.getElementById('generateDocBtn');
  if (generateBtn) {
    generateBtn.onclick = () => {
      generateDocument(window.currentDocType || '民事起诉状');
    };
  }
  // 历史侧边栏
  const historyBtn = document.getElementById('docHistoryBtn');
  if(historyBtn) {
    historyBtn.onclick = () => {
      const sidebar = document.getElementById('documentHistorySidebar');
      if(sidebar) {
        const isOpen = sidebar.style.right === '0px';
        sidebar.style.right = isOpen ? '-300px' : '0px';
      }
    };
  }
  // 弹窗关闭
  const popup = document.getElementById('documentPopup');
  if(popup) {
    popup.addEventListener('click', function(e) {
      if(e.target === this) {
        closeDocumentPopup();
      }
    });
  }
  // 初始化历史
  renderDocumentHistory();
  // 默认选中起诉状
  window.currentDocType = '民事起诉状';
  updateDocTypeUI('民事起诉状');
}

function disableBodyScroll() {
  document.body.style.overflow = 'hidden';
}
function enableBodyScroll() {
  document.body.style.overflow = '';
}

// 监听页面切换，只有在显示文书生成页面时禁止滚动
function observeDocPage() {
  const docPage = document.getElementById('page-doc');
  const observer = new MutationObserver(() => {
    if (docPage && docPage.style.display !== 'none') {
      disableBodyScroll();
    } else {
      enableBodyScroll();
    }
  });
  observer.observe(docPage, { attributes: true, attributeFilter: ['style'] });
}

document.addEventListener('DOMContentLoaded', function() {
  initDocument();
  observeDocPage();
});
