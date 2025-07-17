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
      
      // 管理背景和覆盖层
      const body = document.body;
      const overlay = document.getElementById('home-overlay');
      
      if (page === 'page-home') {
        // 首页：显示背景图片和覆盖层
        body.classList.add('home-page');
        overlay.style.display = 'block';
      } else {
        // 其他页面：移除背景图片，隐藏覆盖层
        body.classList.remove('home-page');
        overlay.style.display = 'none';
      }
    };
  });
}

// 首页法律法规案例卡片假数据
const lawData = {
  newLaws: [
    { title: '个人信息保护法', label: '2021', desc: '加强个人信息保护' },
    { title: '反食品浪费法', label: '2021', desc: '遏制食品浪费' },
    { title: '数据安全法', label: '2021', desc: '数据合规新要求' },
    { title: '未成年人保护法', label: '2020', desc: '保护未成年人权益' },
    { title: '民法典', label: '2021', desc: '社会生活百科全书' },
    { title: '劳动合同法', label: '2019', desc: '规范劳动关系' },
    { title: '婚姻法', label: '2018', desc: '婚姻家庭规范' }
  ],
  newRegulations: [
    { title: '网络直播营销管理办法', label: '2022', desc: '规范网络直播' },
    { title: '互联网广告管理暂行办法', label: '2023', desc: '广告合规' },
    { title: '个人信息出境标准合同办法', label: '2023', desc: '数据跨境合规' },
    { title: '医疗器械监督管理条例', label: '2021', desc: '医疗器械监管' },
    { title: '食品安全国家标准', label: '2022', desc: '食品安全' },
    { title: '住房租赁条例', label: '2023', desc: '住房租赁规范' }
  ],
  newCases: [
    { title: '吴某宇故意杀人案', label: '2023', desc: '社会关注度高' },
    { title: '杭州保姆纵火案', label: '2018', desc: '重大刑事案件' },
    { title: '张某明等故意毁损名誉案', label: '2022', desc: '名誉权保护' },
    { title: '郭志诚诈骗案', label: '2021', desc: '金融诈骗' },
    { title: '程三冒贪污案', label: '2020', desc: '职务犯罪' },
    { title: '山东省济南市人民法院污染案', label: '2022', desc: '环境保护' }
  ]
};

function renderLawCards(filter = '', type = 'all') {
  function renderList(list, elId) {
    const el = document.getElementById(elId);
    el.innerHTML = '';
    list.filter(item => {
      const matchType = (type === 'all') ||
        (type === 'law' && elId === 'list-new-laws') ||
        (type === 'regulation' && elId === 'list-new-regulations') ||
        (type === 'case' && elId === 'list-new-cases');
      return matchType && (!filter || item.title.includes(filter) || item.desc.includes(filter));
    }).forEach(item => {
      el.innerHTML += `<div class=\"law-card-item law-entry\"><div style=\"display:flex;align-items:center;margin-bottom:4px;\"><img src='image/火苗.png' class='law-fire-icon' alt='火苗' /><span class='law-entry-title'>${item.title}</span></div><div style=\"padding-left:22px;\"><span class='law-entry-desc'>${item.desc}</span></div></div>`;
    });
  }
  renderList(lawData.newLaws, 'list-new-laws');
  renderList(lawData.newRegulations, 'list-new-regulations');
  renderList(lawData.newCases, 'list-new-cases');
}

// 词条悬停/点击时显示全部内容（不再显示详情按钮）
function showFullLawEntry(entry) {
  const title = entry.querySelector('.law-entry-title');
  title.style.whiteSpace = 'normal';
  title.style.overflow = 'visible';
  title.style.textOverflow = 'clip';
  // 不改变字体大小和位置
  title.style.background = '#f7faff';
  title.style.padding = '0';
  title.style.borderRadius = '0';
}
function hideFullLawEntry(entry) {
  const title = entry.querySelector('.law-entry-title');
  title.style.whiteSpace = 'nowrap';
  title.style.overflow = 'hidden';
  title.style.textOverflow = 'ellipsis';
  // 不改变字体大小和位置
  title.style.background = 'none';
  title.style.padding = '0';
  title.style.borderRadius = '0';
}
// 首页年龄段饼状图
function drawAgePieChart() {
  const canvas = document.getElementById('agePieChart');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  // 示例数据：18岁以下、18-30岁、31-45岁、46岁及以上
  const data = [12, 38, 32, 18]; // 百分比
  const colors = ['#E5E5E1', '#6B8E7A', '#828FA2', '#9CC3DF'];
  let start = -Math.PI / 2;
  data.forEach((val, i) => {
    const angle = (val / 100) * Math.PI * 2;
    ctx.beginPath();
    ctx.moveTo(110, 110);
    ctx.arc(110, 110, 90, start, start + angle, false);
    ctx.closePath();
    ctx.fillStyle = colors[i];
    ctx.fill();
    start += angle;
  });
}
// 搜索联动后端/law_search
async function searchLawApi(query) {
      const resp = await fetch('http://127.0.0.1:8000/law_search', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query })
  });
  return await resp.json();
}
function showSearchResult(results) {
  document.getElementById('law-card-multi').style.display = 'none';
  document.getElementById('law-card-search-result').style.display = '';
  const list = document.getElementById('search-result-list');
  list.innerHTML = '';
  if (results && results.length) {
    results.forEach(item => {
      list.innerHTML += `<div class="law-card-item"><span class="law-entry-title">${item}</span></div>`;
    });
  } else {
    list.innerHTML = '<div style="color:#888;">未检索到相关内容</div>';
  }
}
function showDefaultCards() {
  document.getElementById('law-card-multi').style.display = '';
  document.getElementById('law-card-search-result').style.display = 'none';
}
// 页面加载完成后初始化
// 搜索标签切换交互
let currentSearchType = 'all';
document.addEventListener('DOMContentLoaded', function() {
  initNavigation();
  renderLawCards();
  drawAgePieChart();
  
  // 初始化背景状态 - 默认显示首页背景
  document.body.classList.add('home-page');
  document.getElementById('home-overlay').style.display = 'block';
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
      const res = await searchLawApi(kw);
      showSearchResult(res.results);
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
}); 
