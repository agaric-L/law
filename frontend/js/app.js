// SPA导航切换
const navs = [
  {btn: 'nav-home', page: 'page-home'},
  {btn: 'nav-ai', page: 'page-ai'},
  {btn: 'nav-contract', page: 'page-contract'},
  {btn: 'nav-doc', page: 'page-doc'},
  {btn: 'nav-quiz', page: 'page-quiz'},
  {btn: 'nav-court', page: 'page-court'}
];

// 初始化导航
function initNavigation() {
  navs.forEach(({btn, page}) => {
    document.getElementById(btn).onclick = function() {
      navs.forEach(({btn, page}) => {
        document.getElementById(btn).classList.remove('active');
        document.getElementById(page).style.display = 'none';
      });
      this.classList.add('active');
      document.getElementById(page).style.display = '';
    };
  });
}

// 词条悬停/点击时显示全部内容（不再显示详情按钮）
function showFullLawEntry(entry) {
  const title = entry.querySelector('.law-entry-title');
  title.style.whiteSpace = 'normal';
  title.style.overflow = 'visible';
  title.style.textOverflow = 'clip';
  title.style.fontSize = '13px';
  title.style.background = '#f7faff';
  title.style.padding = '2px 4px';
  title.style.borderRadius = '4px';
}
function hideFullLawEntry(entry) {
  const title = entry.querySelector('.law-entry-title');
  title.style.whiteSpace = 'nowrap';
  title.style.overflow = 'hidden';
  title.style.textOverflow = 'ellipsis';
  title.style.fontSize = '15px';
  title.style.background = 'none';
  title.style.padding = '0';
  title.style.borderRadius = '0';
}


// 搜索联动后端/law_search
async function searchLawApi(query) {
  console.log("***************");
  const resp = await fetch('http://localhost:8000/law_search', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query })
  });
  console.log(resp);
  return await resp.json();
}
function showSearchResult(results) {
  document.getElementById('law-card-multi').style.display = 'none';
  document.getElementById('law-card-search-result').style.display = '';
  const list = document.getElementById('search-result-list');
  list.innerHTML = '';

  // 优先渲染raw_results
  let laws = [];
  // 检查多种可能的数据结构
  if (Array.isArray(results?.raw_results) && results.raw_results.length) {
    laws = results.raw_results.filter(item => item.type === 'law');
  } else if (Array.isArray(results?.summary?.laws)) {
    laws = results.summary.laws;
  } else if (results?.laws && Array.isArray(results.laws)) {
    laws = results.laws;
  }

      // 渲染法律法规区
  if (laws.length) {
    // 重新处理法条内容，保证每个条目只显示自己的内容
    const processedLaws = [];
    const titleRegex = /第[\d一二三四五六七八九十百千万]+条.*?/;
    
    // 首先收集所有的原始数据
    laws.forEach(law => {
      let title = law.title || law.name || '';
      let allContent = '';
      
      if (law.details && Array.isArray(law.details)) {
        allContent = law.details.join('\n');
      } else if (law.content) {
        allContent = law.content;
      } else if (law.detail) {
        allContent = law.detail;
      }
      
      // 将标题与内容放入处理队列
      processedLaws.push({
        title: title,
        content: allContent
      });
    });
    
         // 为每个条目正确分配内容
     for (let i = 0; i < processedLaws.length; i++) {
       const currentLaw = processedLaws[i];
       
       // 如果是从API返回的raw_results处理
       if (laws[i].details && Array.isArray(laws[i].details)) {
         // 直接使用详细内容，不做过滤，只要确保不重复标题即可
         let details = laws[i].details.filter(d => d.trim() !== currentLaw.title);
         processedLaws[i].content = details.join('\n');
         continue;
       }
       
       // 如果是其他格式，则按标题分割
       let contentLines = currentLaw.content.split('\n');
       let cleanContent = [];
       let foundNextTitle = false;
       
       // 查找下一个标题的位置
       for (let j = 0; j < contentLines.length; j++) {
         const line = contentLines[j].trim();
         if (!line) continue;
         
         // 检查是否为下一个法条的标题
         const isNextTitle = titleRegex.test(line) && 
                             line !== currentLaw.title && 
                             line.startsWith('第');
                             
         if (isNextTitle && j > 0) { // 找到下一个标题，但不是第一行
           foundNextTitle = true;
           // 保留之前的所有内容
           cleanContent = contentLines.slice(0, j).filter(l => l.trim() && l.trim() !== currentLaw.title);
           break;
         }
       }
       
       // 如果没有找到下一个标题，保留所有内容
       if (!foundNextTitle) {
         cleanContent = contentLines.filter(l => l.trim() && l.trim() !== currentLaw.title);
       }
       
       // 更新处理后的内容
       processedLaws[i].content = cleanContent.join('\n');
    }
    
    // 渲染处理后的法条数据
    processedLaws.forEach((law, idx) => {
      let title = law.title;
      let content = law.content;
      
      // 如果内容中包含标题，去除标题部分(额外保险措施)
      if (content.startsWith(title)) {
        content = content.slice(title.length).replace(/^[:：\s]*/, '');
      }
      
            // 渲染处理后的条目
      list.innerHTML += `<div style='margin-bottom:0;padding:18px 0;${idx !== 0 ? "border-top:1px dashed #bbb;" : ''}'>
        <div style='font-size:18px;font-weight:600;line-height:1.5;margin-bottom:8px;'>${title}</div>
        <div style='color:#444;font-size:15px;line-height:1.9;font-weight:normal;white-space:pre-line;'>${content}</div>
      </div>`;
    });
  } else {
    list.innerHTML += `<div style='color:#bbb;margin-bottom:18px;'>暂无相关法律法规</div>`;
  }
}




function showDefaultCards() {
  document.getElementById('law-card-multi').style.display = '';
  document.getElementById('law-card-search-result').style.display = 'none';
}

async function fetchCaseCards(forceRefresh = false) {
  try {
    const url = `http://localhost:8000/api/case_cards${forceRefresh ? '?force_refresh=true' : ''}`;
    const resp = await fetch(url);
    return await resp.json();
  } catch (error) {
    console.error('获取案例卡片数据失败:', error);
    return {};
  }
}

function renderCaseCards(data) {
  console.log('案例卡片数据:', data);
  
  // 后端返回的数据结构映射到前端卡片ID
  const typeMap = {
    "刑事案件": "criminal",
    "民事案件": "civil",
    "商事案件": "commercial",
    "行政案件": "administrative",
    "环资案件": "environment"
  };
  
  // 遍历五种案例类型
  Object.keys(typeMap).forEach(type => {
    const el = document.getElementById('list-' + typeMap[type]);
    if (!el) {
      console.error(`找不到元素: list-${typeMap[type]}`);
      return;
    }
    
    el.innerHTML = '';
    
    // 确保数据存在且有caseList
    if (!data[type] || !data[type].caseList || !Array.isArray(data[type].caseList)) {
      el.innerHTML = '<div class="case-item">暂无数据</div>';
      return;
    }
    
    // 渲染案例列表
    const caseList = data[type].caseList;
    caseList.forEach(item => {
      // 使用caseName作为标题，caseOverview作为描述
      const title = item.caseName || '';
      const desc = item.caseOverview || '';
      // 使用caseUrl作为链接，如果没有则使用默认链接
      const url = item.caseUrl || 'https://eastlawlibrary.court.gov.cn/court-digital-library-search/page/caseFilesDatabase/imageCaseDetail.html';
      
      el.innerHTML += `
        <div class="case-item" onclick="window.open('${url}', '_blank')">
          <div class="case-title">
            <span class="case-fire"><img src="image/火苗.png" alt="热门" style="width: 16px; height: 16px; vertical-align: middle;"></span>
            <span>${title}</span>
          </div>
          <div class="case-desc">${desc}</div>
        </div>
      `;
    });
  });
}

// 页面加载时自动拉取
// 搜索标签切换交互
let currentSearchType = 'all';
document.addEventListener('DOMContentLoaded', async function() {
  initNavigation();
  // renderLawCards(); // 注释掉原有三卡片渲染
  // drawAgePieChart(); // 如无用可注释
  // 标签切换
  document.querySelectorAll('.law-search-tab').forEach(tab => {
    tab.onclick = function() {
      document.querySelectorAll('.law-search-tab').forEach(t => t.classList.remove('active'));
      this.classList.add('active');
      currentSearchType = this.getAttribute('data-type');
    };
  });
  document.getElementById('law-search-btn').onclick = async function() {
    const kw = document.getElementById('law-search-input').value.trim();
    if (kw) {
      try {
        const res = await searchLawApi(kw);
        if (res && res.results) {
          // 传递整个结果对象，而不只是summary部分
          showSearchResult(res.results);
        } else {
          // 处理无结果的情况
          console.error('未获取到有效结果数据');
          document.getElementById('search-result-list').innerHTML = `<div style='color:#bbb;margin-bottom:18px;'>暂无相关法律法规</div>`;
          document.getElementById('law-card-multi').style.display = 'none';
          document.getElementById('law-card-search-result').style.display = '';
        }
      } catch (error) {
        console.error('搜索请求失败:', error);
        document.getElementById('search-result-list').innerHTML = `<div style='color:#bbb;margin-bottom:18px;'>搜索请求失败，请稍后重试</div>`;
        document.getElementById('law-card-multi').style.display = 'none';
        document.getElementById('law-card-search-result').style.display = '';
      }
    } else {
      showDefaultCards();
    }
  };
  document.getElementById('law-search-input').addEventListener('input', function() {
    if (!this.value.trim()) showDefaultCards();
  });
  // 词条悬停/点击显示全部内容
  document.body.addEventListener('mouseover', function(e) {
    if (e.target.classList.contains('law-entry-title')) {
      showFullLawEntry(e.target.parentElement);
    }
  });
  document.body.addEventListener('mouseout', function(e) {
    if (e.target.classList.contains('law-entry-title')) {
      hideFullLawEntry(e.target.parentElement);
    }
  });
  document.body.addEventListener('click', function(e) {
    if (e.target.classList.contains('law-entry-title')) {
      showFullLawEntry(e.target.parentElement);
    }
  });
  // ========== 新五张卡片渲染 ========== 
  const caseData = await fetchCaseCards(true); // 首次加载强制刷新
  renderCaseCards(caseData);
}); 