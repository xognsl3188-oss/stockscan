"""
STOCKSCAN — 실시간 주식 기술적 분석기 (Finnhub API)
=====================================================
실행 방법:
  1. 라이브러리 설치:  pip install flask pandas numpy requests
  2. 환경변수 설정:    set FINNHUB_API_KEY=your_api_key
  3. 실행:             python stockscan.py
  4. 브라우저에서:     http://localhost:5000
"""

from flask import Flask, jsonify, request
import pandas as pd
import numpy as np
import requests
import os
import datetime

app = Flask(__name__)

FINNHUB_KEY = os.environ.get('FINNHUB_API_KEY', '')

HTML = """<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>STOCKSCAN — 실시간 기술적 분석기</title>
<link href="https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=Bebas+Neue&family=Noto+Sans+KR:wght@300;400;700&display=swap" rel="stylesheet">
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.0/chart.umd.min.js"></script>
<style>
  :root {
    --bg: #080c10; --surface: #0d1117; --border: #1e2a38;
    --accent: #00ff88; --danger: #ff3b5c; --warn: #ffb800;
    --text: #c9d1d9; --muted: #4a5568;
    --glow: 0 0 20px rgba(0,255,136,0.3);
    --glow-red: 0 0 20px rgba(255,59,92,0.3);
  }
  * { margin:0; padding:0; box-sizing:border-box; }
  body { background:var(--bg); color:var(--text); font-family:'Noto Sans KR',sans-serif; min-height:100vh; }
  body::before {
    content:''; position:fixed; inset:0;
    background:repeating-linear-gradient(0deg,transparent,transparent 2px,rgba(0,0,0,0.03) 2px,rgba(0,0,0,0.03) 4px);
    pointer-events:none; z-index:9999;
  }
  header {
    border-bottom:1px solid var(--border); padding:1.5rem 2rem;
    display:flex; align-items:center; gap:1rem;
    background:rgba(13,17,23,0.9); backdrop-filter:blur(10px);
    position:sticky; top:0; z-index:100;
  }
  .logo { font-family:'Bebas Neue',sans-serif; font-size:2rem; color:var(--accent); letter-spacing:4px; text-shadow:var(--glow); }
  .logo span { color:var(--text); opacity:0.5; }
  .live-badge {
    margin-left:auto; display:flex; align-items:center; gap:0.5rem;
    font-family:'Space Mono',monospace; font-size:0.65rem; color:var(--accent);
  }
  .dot { width:8px; height:8px; border-radius:50%; background:var(--accent); animation:pulse 2s infinite; }
  @keyframes pulse { 0%,100%{opacity:1;transform:scale(1)} 50%{opacity:0.5;transform:scale(0.8)} }

  main { max-width:900px; margin:0 auto; padding:2rem; }

  .search-section {
    background:var(--surface); border:1px solid var(--border);
    border-radius:4px; padding:1.5rem; margin-bottom:1.5rem;
    position:relative; overflow:hidden;
  }
  .search-section::before {
    content:''; position:absolute; top:0; left:0; right:0; height:2px;
    background:linear-gradient(90deg,transparent,var(--accent),transparent);
    animation:scan 3s linear infinite;
  }
  @keyframes scan { 0%{transform:translateX(-100%)} 100%{transform:translateX(100%)} }
  .search-label { font-family:'Space Mono',monospace; font-size:0.65rem; color:var(--accent); letter-spacing:3px; margin-bottom:1rem; }
  .search-input {
    width:100%; background:var(--bg); border:1px solid var(--border); border-radius:2px;
    color:var(--text); font-family:'Space Mono',monospace; font-size:1.1rem;
    padding:1rem 1.2rem; outline:none; transition:border-color 0.2s,box-shadow 0.2s;
    text-transform:uppercase; letter-spacing:2px; margin-bottom:1rem;
  }
  .search-input:focus { border-color:var(--accent); box-shadow:var(--glow); }
  .bottom-row { display:flex; gap:1rem; align-items:center; }
  .market-toggle { display:flex; border:1px solid var(--border); border-radius:2px; overflow:hidden; }
  .market-btn {
    padding:0.8rem 1.5rem; background:transparent; border:none; cursor:pointer;
    font-family:'Space Mono',monospace; font-size:0.75rem; color:var(--muted); transition:all 0.2s;
  }
  .market-btn.active { background:var(--accent); color:var(--bg); font-weight:700; }
  .analyze-btn {
    flex:1; padding:0.9rem; background:var(--accent); color:var(--bg); border:none;
    border-radius:2px; font-family:'Bebas Neue',sans-serif; font-size:1.3rem;
    letter-spacing:3px; cursor:pointer; transition:all 0.2s;
  }
  .analyze-btn:hover { opacity:0.9; transform:translateY(-1px); }
  .analyze-btn:disabled { opacity:0.4; cursor:not-allowed; transform:none; }
  .quick-picks { margin-top:1rem; display:flex; gap:0.5rem; flex-wrap:wrap; align-items:center; }
  .qpick-label { font-family:'Space Mono',monospace; font-size:0.6rem; color:var(--muted); }
  .quick-btn {
    padding:0.3rem 0.8rem; background:transparent; border:1px solid var(--border);
    border-radius:2px; color:var(--muted); font-family:'Space Mono',monospace;
    font-size:0.65rem; cursor:pointer; transition:all 0.2s;
  }
  .quick-btn:hover { border-color:var(--accent); color:var(--accent); }

  .loading { text-align:center; padding:4rem; display:none; }
  .loading-text { font-family:'Space Mono',monospace; font-size:0.75rem; color:var(--accent); letter-spacing:3px; animation:blink 1s infinite; }
  @keyframes blink { 0%,100%{opacity:1} 50%{opacity:0.3} }
  .loading-bar { width:200px; height:2px; background:var(--border); margin:1rem auto; border-radius:1px; overflow:hidden; }
  .loading-fill { height:100%; background:var(--accent); animation:ld 1.5s ease-in-out infinite; }
  @keyframes ld { 0%{width:0;margin-left:0} 50%{width:100%;margin-left:0} 100%{width:0;margin-left:100%} }

  #results { display:none; animation:fadeIn 0.4s ease; }
  @keyframes fadeIn { from{opacity:0;transform:translateY(10px)} to{opacity:1;transform:translateY(0)} }

  .verdict-card { padding:2rem; border-radius:4px; margin-bottom:1.5rem; border:1px solid; }
  .verdict-card.buy { border-color:var(--accent); background:rgba(0,255,136,0.04); }
  .verdict-card.sell { border-color:var(--danger); background:rgba(255,59,92,0.04); }
  .verdict-card.hold { border-color:var(--warn); background:rgba(255,184,0,0.04); }
  .verdict-header { display:flex; align-items:flex-start; gap:2rem; margin-bottom:1.5rem; }
  .verdict-signal { font-family:'Bebas Neue',sans-serif; font-size:3.5rem; line-height:1; letter-spacing:3px; flex-shrink:0; }
  .buy .verdict-signal { color:var(--accent); text-shadow:var(--glow); }
  .sell .verdict-signal { color:var(--danger); text-shadow:var(--glow-red); }
  .hold .verdict-signal { color:var(--warn); }
  .verdict-meta { flex:1; }
  .verdict-ticker { font-family:'Space Mono',monospace; font-size:1.1rem; color:var(--muted); }
  .verdict-name { font-size:1.1rem; margin:0.3rem 0; }
  .verdict-price { font-family:'Space Mono',monospace; font-size:2rem; font-weight:700; }
  .verdict-change { font-family:'Space Mono',monospace; font-size:0.85rem; margin-top:0.3rem; }
  .pos { color:var(--accent); } .neg { color:var(--danger); }
  .conf-label { font-family:'Space Mono',monospace; font-size:0.6rem; color:var(--muted); letter-spacing:3px; margin-bottom:0.5rem; }
  .conf-bar { height:3px; background:var(--border); border-radius:2px; }
  .conf-fill { height:100%; border-radius:2px; transition:width 1s ease; }
  .buy .conf-fill { background:var(--accent); } .sell .conf-fill { background:var(--danger); } .hold .conf-fill { background:var(--warn); }

  .indicators-grid { display:grid; grid-template-columns:repeat(3,1fr); gap:1rem; margin-bottom:1.5rem; }
  @media(max-width:600px) { .indicators-grid { grid-template-columns:repeat(2,1fr); } }
  .ind-card { background:var(--surface); border:1px solid var(--border); border-radius:4px; padding:1.2rem; }
  .ind-name { font-family:'Space Mono',monospace; font-size:0.65rem; color:var(--muted); letter-spacing:2px; margin-bottom:0.5rem; }
  .ind-value { font-family:'Space Mono',monospace; font-size:1.1rem; font-weight:700; }
  .ind-signal { font-size:0.75rem; margin-top:0.3rem; font-family:'Space Mono',monospace; }
  .ind-desc { margin-top:0.6rem; font-size:0.75rem; color:var(--muted); line-height:1.6; border-top:1px solid var(--border); padding-top:0.6rem; }
  .sig-buy { color:var(--accent); } .sig-sell { color:var(--danger); } .sig-neutral { color:var(--warn); }

  .chart-section { background:var(--surface); border:1px solid var(--border); border-radius:4px; padding:1.5rem; margin-bottom:1.5rem; }
  .chart-title { font-family:'Space Mono',monospace; font-size:0.65rem; color:var(--accent); letter-spacing:3px; margin-bottom:1rem; }
  #priceChart { max-height:300px; }

  .summary-box { background:var(--surface); border:1px solid var(--border); border-radius:4px; padding:1.5rem; margin-bottom:1.5rem; }
  .summary-title { font-family:'Space Mono',monospace; font-size:0.65rem; color:var(--muted); letter-spacing:3px; margin-bottom:1rem; }
  .summary-text { font-size:0.95rem; line-height:1.8; }

  .news-section { background:var(--surface); border:1px solid var(--border); border-radius:4px; padding:1.5rem; margin-bottom:1.5rem; }
  .news-title { font-family:'Space Mono',monospace; font-size:0.65rem; color:var(--accent); letter-spacing:3px; margin-bottom:1rem; }
  .news-item { padding:0.8rem 0; border-bottom:1px solid var(--border); display:flex; gap:0.8rem; align-items:flex-start; }
  .news-item:last-child { border-bottom:none; }
  .news-badge { font-family:'Space Mono',monospace; font-size:0.6rem; padding:0.2rem 0.5rem; border-radius:2px; flex-shrink:0; font-weight:700; }
  .badge-호재 { background:rgba(0,255,136,0.15); color:var(--accent); border:1px solid var(--accent); }
  .badge-악재 { background:rgba(255,59,92,0.15); color:var(--danger); border:1px solid var(--danger); }
  .badge-중립 { background:rgba(74,85,104,0.3); color:var(--muted); border:1px solid var(--muted); }
  .news-content { flex:1; }
  .news-headline { font-size:0.85rem; line-height:1.5; color:var(--text); text-decoration:none; }
  .news-headline:hover { color:var(--accent); }
  .news-meta { font-family:'Space Mono',monospace; font-size:0.6rem; color:var(--muted); margin-top:0.3rem; }

  .error-box { background:rgba(255,59,92,0.08); border:1px solid var(--danger); border-radius:4px; padding:1.5rem; color:var(--danger); font-family:'Space Mono',monospace; font-size:0.8rem; line-height:1.8; margin-bottom:1.5rem; }

  .disclaimer { padding:1rem; border:1px solid var(--border); border-radius:2px; font-family:'Space Mono',monospace; font-size:0.6rem; color:var(--muted); line-height:1.8; margin-bottom:1rem; }

  .footer-support {
    margin-top:2rem; padding:1.5rem 2rem;
    border:1px solid var(--border); border-radius:4px;
    text-align:center; background:var(--surface);
  }
  .footer-support .made-by { font-family:'Space Mono',monospace; font-size:0.6rem; color:var(--muted); letter-spacing:2px; margin-bottom:0.8rem; }
  .footer-support .support-msg { font-size:0.85rem; color:var(--text); margin-bottom:0.8rem; line-height:1.6; }
  .footer-support .account { font-family:'Space Mono',monospace; font-size:0.9rem; color:var(--accent); letter-spacing:1px; padding:0.6rem 1.2rem; border:1px solid var(--accent); border-radius:4px; display:inline-block; margin-top:0.3rem; }
</style>
</head>
<body>
<header>
  <div class="logo">STOCK<span>SCAN</span></div>
  <div class="live-badge"><div class="dot"></div>LIVE DATA</div>
</header>
<main>
  <div class="search-section">
    <div class="search-label">▶ 종목 입력 / TICKER SYMBOL</div>
    <input class="search-input" id="tickerInput" placeholder="예: IBM, AAPL, 005930 (삼성전자)" autocomplete="off" autocorrect="off" spellcheck="false" />
    <div class="bottom-row">
      <div class="market-toggle">
        <button class="market-btn active" id="btnUS" onclick="setMarket('US')">🇺🇸 US</button>
        <button class="market-btn" id="btnKR" onclick="setMarket('KR')">🇰🇷 KR</button>
      </div>
      <button class="analyze-btn" id="analyzeBtn" onclick="analyze()">SCAN</button>
    </div>
    <div class="quick-picks">
      <span class="qpick-label">빠른 선택:</span>
      <button class="quick-btn" onclick="quick('IBM','US')">IBM</button>
      <button class="quick-btn" onclick="quick('AAPL','US')">AAPL</button>
      <button class="quick-btn" onclick="quick('NVDA','US')">NVDA</button>
      <button class="quick-btn" onclick="quick('TSLA','US')">TSLA</button>
      <button class="quick-btn" onclick="quick('META','US')">META</button>
      <button class="quick-btn" onclick="quick('005930','KR')">삼성전자</button>
      <button class="quick-btn" onclick="quick('000660','KR')">SK하이닉스</button>
      <button class="quick-btn" onclick="quick('035420','KR')">NAVER</button>
      <button class="quick-btn" onclick="quick('035720','KR')">카카오</button>
    </div>
  </div>

  <div class="loading" id="loading">
    <div class="loading-text">FETCHING REAL-TIME DATA...</div>
    <div class="loading-bar"><div class="loading-fill"></div></div>
    <div class="loading-text" style="font-size:0.55rem;margin-top:0.5rem;color:var(--muted)">RSI · MACD · 볼린저밴드 · 이동평균 계산중</div>
  </div>

  <div id="results"></div>

  <div class="disclaimer">
    ⚠ 본 서비스는 기술적 분석 기반의 참고용 정보를 제공하며, 투자 권유가 아닙니다. 실제 투자 결정은 본인의 판단과 책임 하에 이루어져야 합니다. 과거 패턴이 미래 수익을 보장하지 않습니다.
  </div>

  <div class="footer-support">
    <div class="made-by">MADE BY 김태훈</div>
    <div class="support-msg">
      무료로 배포 가능하나, 도움이 되셨다면 후원 부탁드립니다 🙏<br>
      소중한 후원이 서비스 유지에 큰 힘이 됩니다!
    </div>
    <div class="account">카카오뱅크 3333-03-5584101 · 김태훈</div>
  </div>
</main>

<script>
let currentMarket = 'US';
let priceChart = null;

function setMarket(m) {
  currentMarket = m;
  document.getElementById('btnUS').classList.toggle('active', m==='US');
  document.getElementById('btnKR').classList.toggle('active', m==='KR');
}

function quick(t, m) {
  document.getElementById('tickerInput').value = t;
  setMarket(m);
  analyze();
}

async function analyze() {
  let ticker = document.getElementById('tickerInput').value.trim().toUpperCase();
  if(!ticker) { alert('종목명을 입력해주세요!'); return; }
  if(currentMarket === 'KR' && !ticker.includes(':')) ticker = 'KRX:' + ticker;

  document.getElementById('results').style.display = 'none';
  document.getElementById('loading').style.display = 'block';
  document.getElementById('analyzeBtn').disabled = true;

  try {
    const res = await fetch('/analyze?ticker=' + encodeURIComponent(ticker));
    const data = await res.json();
    document.getElementById('loading').style.display = 'none';
    if(data.error) {
      document.getElementById('results').innerHTML = `<div class="error-box">❌ ${data.error}<br><br>미국 주식: AAPL, IBM, TSLA<br>한국 주식: KR 선택 후 005930 입력</div>`;
      document.getElementById('results').style.display = 'block';
    } else {
      renderResults(data);
    }
  } catch(e) {
    document.getElementById('loading').style.display = 'none';
    document.getElementById('results').innerHTML = `<div class="error-box">❌ 서버 연결 오류: ${e.message}</div>`;
    document.getElementById('results').style.display = 'block';
  }
  document.getElementById('analyzeBtn').disabled = false;
}

function renderResults(d) {
  const signalMap = {'매수':'▲ BUY','매도':'▼ SELL','관망':'◆ HOLD'};
  const clsMap = {'매수':'buy','매도':'sell','관망':'hold'};
  const cls = clsMap[d.verdict];
  const signalEn = signalMap[d.verdict];

  const indDesc = {
    'RSI': 'RSI(상대강도지수)는 0~100 값으로 과매수/과매도를 측정해요. 30 이하면 과매도(반등 가능), 70 이상이면 과매수(조정 가능) 신호예요.',
    '이동평균': '단기(5일)·중기(20일)·장기(60일) 평균 주가를 비교해요. 단기선이 장기선 위로 올라서면 골든크로스(상승신호), 아래로 내려가면 데드크로스(하락신호)예요.',
    '볼린저밴드': '평균과 표준편차로 상·하단 밴드를 만들어요. 하단 밴드 근처면 저점 반등 가능성, 상단 밴드 근처면 과열 신호예요.',
    'MACD': '단기·장기 이동평균 차이로 추세 전환을 포착해요. 히스토그램이 양수로 전환되면 상승 모멘텀, 음수로 전환되면 하락 모멘텀이에요.',
    '거래량': '현재 거래량을 20일 평균과 비교해요. 주가 상승+거래량 급증은 강한 매수 신호, 주가 하락+거래량 급증은 강한 매도 신호예요.',
    '지지/저항': '최근 20일 최저가(지지선)와 최고가(저항선)를 봐요. 지지선 근처면 반등 가능, 저항선 근처면 조정 가능성이 높아요.'
  };

  const indsHTML = d.indicators.map(s => {
    const sc = s.verdict==='매수'?'sig-buy':s.verdict==='매도'?'sig-sell':'sig-neutral';
    const ic = s.verdict==='매수'?'▲':s.verdict==='매도'?'▼':'◆';
    const desc = indDesc[s.name] || '';
    return `<div class="ind-card">
      <div class="ind-name">${s.name}</div>
      <div class="ind-value ${sc}">${ic} ${s.verdict}</div>
      <div class="ind-signal ${sc}">${s.detail}</div>
      <div class="ind-desc">${desc}</div>
    </div>`;
  }).join('');

  const chg = d.price_change >= 0;
  document.getElementById('results').innerHTML = `
    <div class="verdict-card ${cls}">
      <div class="verdict-header">
        <div class="verdict-signal">${signalEn}</div>
        <div class="verdict-meta">
          <div class="verdict-ticker">${d.ticker}</div>
          <div class="verdict-name">${d.name || ''}</div>
          <div class="verdict-price">${d.price_fmt}</div>
          <div class="verdict-change ${chg?'pos':'neg'}">${chg?'+':''}${d.price_change.toFixed(2)}% (전일대비)</div>
        </div>
        <div style="text-align:right">
          <div style="font-family:'Space Mono',monospace;font-size:0.65rem;color:var(--muted);margin-bottom:0.3rem">BUY ${d.buy_score} vs SELL ${d.sell_score}</div>
          <div style="font-family:'Space Mono',monospace;font-size:1.8rem;color:var(--${cls==='buy'?'accent':cls==='sell'?'danger':'warn'})">${d.confidence.toFixed(0)}%</div>
          <div style="font-family:'Space Mono',monospace;font-size:0.6rem;color:var(--muted)">신뢰도</div>
        </div>
      </div>
      <div class="conf-label">SIGNAL CONFIDENCE</div>
      <div class="conf-bar"><div class="conf-fill" style="width:${d.confidence}%"></div></div>
    </div>

    <div class="indicators-grid">${indsHTML}</div>

    <div class="chart-section">
      <div class="chart-title">▶ 60일 실제 가격 차트 + 이동평균선</div>
      <canvas id="priceChart"></canvas>
    </div>

    <div class="summary-box">
      <div class="summary-title">▶ 종합 분석 의견</div>
      <div class="summary-text">${d.summary}</div>
    </div>
  `;
  document.getElementById('results').style.display = 'block';
  setTimeout(() => drawChart(d), 100);

  // 뉴스
  fetch('/news?ticker=' + encodeURIComponent(d.ticker))
    .then(r => r.json())
    .then(newsData => {
      if(newsData.news && newsData.news.length > 0) {
        const newsHTML = newsData.news.map(n => {
          const badgeClass = 'badge-' + n.sentiment;
          return `<div class="news-item">
            <span class="news-badge ${badgeClass}">${n.sentiment}</span>
            <div class="news-content">
              <a href="${n.link}" target="_blank" class="news-headline">${n.title}</a>
              <div class="news-meta">${n.publisher} · ${n.date}</div>
            </div>
          </div>`;
        }).join('');
        const newsSection = `<div class="news-section">
          <div class="news-title">▶ 최근 뉴스 (호재 / 악재)</div>
          ${newsHTML}
        </div>`;
        document.getElementById('results').insertAdjacentHTML('beforeend', newsSection);
      }
    }).catch(() => {});
}

function drawChart(d) {
  if(priceChart) { priceChart.destroy(); priceChart=null; }
  const ctx = document.getElementById('priceChart');
  if(!ctx) return;
  priceChart = new Chart(ctx, {
    type:'line',
    data:{
      labels: d.dates,
      datasets:[
        { label:'주가', data:d.prices, borderColor:'rgba(201,209,217,0.8)', backgroundColor:'rgba(201,209,217,0.05)', borderWidth:1.5, pointRadius:0, fill:true, tension:0.3 },
        { label:'MA5', data:d.ma5, borderColor:'#00ff88', borderWidth:1.5, pointRadius:0, fill:false, tension:0.3 },
        { label:'MA20', data:d.ma20, borderColor:'#ffb800', borderWidth:1.5, pointRadius:0, fill:false, tension:0.3, borderDash:[5,3] },
        { label:'볼린저상단', data:d.bb_upper, borderColor:'rgba(255,59,92,0.4)', borderWidth:1, pointRadius:0, fill:false, tension:0.3, borderDash:[3,3] },
        { label:'볼린저하단', data:d.bb_lower, borderColor:'rgba(0,255,136,0.4)', borderWidth:1, pointRadius:0, fill:false, tension:0.3, borderDash:[3,3] },
      ]
    },
    options:{
      responsive:true, maintainAspectRatio:true,
      interaction:{mode:'index',intersect:false},
      plugins:{ legend:{ labels:{ color:'#4a5568', font:{family:'Space Mono',size:10} } } },
      scales:{
        x:{ ticks:{color:'#4a5568',maxTicksLimit:8,font:{family:'Space Mono',size:9}}, grid:{color:'rgba(30,42,56,0.8)'} },
        y:{ ticks:{color:'#4a5568',font:{family:'Space Mono',size:9}}, grid:{color:'rgba(30,42,56,0.8)'} }
      }
    }
  });
}

document.getElementById('tickerInput').addEventListener('keypress', e => { if(e.key==='Enter') analyze(); });
</script>
</body>
</html>
"""

def calc_rsi(prices, period=14):
    delta = prices.diff()
    gain = delta.clip(lower=0).rolling(period).mean()
    loss = -delta.clip(upper=0).rolling(period).mean()
    rs = gain / loss.replace(0, np.nan)
    return 100 - 100 / (1 + rs)

def calc_macd(prices, fast=12, slow=26, signal=9):
    ema_fast = prices.ewm(span=fast, adjust=False).mean()
    ema_slow = prices.ewm(span=slow, adjust=False).mean()
    macd = ema_fast - ema_slow
    sig = macd.ewm(span=signal, adjust=False).mean()
    return macd, sig, macd - sig

def calc_bollinger(prices, period=20, std=2):
    ma = prices.rolling(period).mean()
    sd = prices.rolling(period).std()
    return ma + std*sd, ma, ma - std*sd

@app.route('/')
def index():
    return HTML

@app.route('/analyze')
def analyze():
    ticker = request.args.get('ticker', '').upper()
    if not ticker:
        return jsonify({'error': '티커를 입력해주세요.'})
    if not FINNHUB_KEY:
        return jsonify({'error': 'API 키가 설정되지 않았습니다. Render 환경변수를 확인해주세요.'})

    try:
        to_ts = int(datetime.datetime.now().timestamp())
        from_ts = to_ts - 60 * 60 * 24 * 100

        url = f"https://finnhub.io/api/v1/stock/candle?symbol={ticker}&resolution=D&from={from_ts}&to={to_ts}&token={FINNHUB_KEY}"
        r = requests.get(url, timeout=10)
        data = r.json()

        if data.get('s') == 'no_data' or not data.get('c'):
            return jsonify({'error': f"'{ticker}' 데이터를 찾을 수 없습니다. 티커 심볼을 확인해주세요."})

        closes = pd.Series(data['c'])
        volumes = pd.Series(data.get('v', [0]*len(data['c'])))
        timestamps = data['t']
        dates = [datetime.datetime.fromtimestamp(t).strftime('%Y-%m-%d') for t in timestamps]

        closes = closes.tail(60).reset_index(drop=True)
        volumes = volumes.tail(60).reset_index(drop=True)
        dates = dates[-60:]

        current = float(closes.iloc[-1])
        prev = float(closes.iloc[-2])
        price_change = (current - prev) / prev * 100
        is_kr = ticker.startswith('KRX:')
        price_fmt = f"{current:,.0f}원" if is_kr else f"${current:,.2f}"

        # 회사 이름
        try:
            profile = requests.get(f"https://finnhub.io/api/v1/stock/profile2?symbol={ticker}&token={FINNHUB_KEY}", timeout=5).json()
            name = profile.get('name', '')
        except:
            name = ''

        rsi = calc_rsi(closes)
        rsi_val = float(rsi.iloc[-1])

        macd_line, signal_line, macd_hist = calc_macd(closes)
        macd_val = float(macd_line.iloc[-1])
        hist_val = float(macd_hist.iloc[-1])

        bb_upper, bb_mid, bb_lower = calc_bollinger(closes)
        bb_u = float(bb_upper.iloc[-1])
        bb_l = float(bb_lower.iloc[-1])
        bb_pos = (current - bb_l) / (bb_u - bb_l) * 100 if (bb_u - bb_l) > 0 else 50

        ma5 = closes.rolling(5).mean()
        ma20 = closes.rolling(20).mean()
        ma60 = closes.rolling(60).mean()
        ma5_val = float(ma5.iloc[-1])
        ma20_val = float(ma20.iloc[-1])
        ma60_val = float(ma60.iloc[-1]) if len(closes) >= 60 else float(ma20.iloc[-1])

        vol = float(volumes.iloc[-1])
        avg_vol = float(volumes.mean())
        vol_ratio = vol / avg_vol if avg_vol > 0 else 1

        support = float(closes.tail(20).min())
        resistance = float(closes.tail(20).max())
        dist_sup = (current - support) / support * 100
        dist_res = (resistance - current) / resistance * 100

        buy_score = 0
        sell_score = 0
        indicators = []

        if rsi_val < 30:
            buy_score += 2
            indicators.append({'name':'RSI', 'verdict':'매수', 'detail':f'{rsi_val:.1f} — 과매도 구간'})
        elif rsi_val > 70:
            sell_score += 2
            indicators.append({'name':'RSI', 'verdict':'매도', 'detail':f'{rsi_val:.1f} — 과매수 구간'})
        else:
            indicators.append({'name':'RSI', 'verdict':'중립', 'detail':f'{rsi_val:.1f} — 중립'})

        if ma5_val > ma20_val and ma20_val > ma60_val:
            buy_score += 2
            indicators.append({'name':'이동평균', 'verdict':'매수', 'detail':'5>20>60 골든크로스'})
        elif ma5_val < ma20_val and ma20_val < ma60_val:
            sell_score += 2
            indicators.append({'name':'이동평균', 'verdict':'매도', 'detail':'5<20<60 데드크로스'})
        else:
            indicators.append({'name':'이동평균', 'verdict':'중립', 'detail':'혼재 신호'})

        if bb_pos < 15:
            buy_score += 1
            indicators.append({'name':'볼린저밴드', 'verdict':'매수', 'detail':f'하단 근접 ({bb_pos:.0f}%)'})
        elif bb_pos > 85:
            sell_score += 1
            indicators.append({'name':'볼린저밴드', 'verdict':'매도', 'detail':f'상단 근접 ({bb_pos:.0f}%)'})
        else:
            indicators.append({'name':'볼린저밴드', 'verdict':'중립', 'detail':f'밴드 중간 ({bb_pos:.0f}%)'})

        if hist_val > 0 and macd_val > 0:
            buy_score += 1
            indicators.append({'name':'MACD', 'verdict':'매수', 'detail':'히스토그램 양전환'})
        elif hist_val < 0 and macd_val < 0:
            sell_score += 1
            indicators.append({'name':'MACD', 'verdict':'매도', 'detail':'히스토그램 음전환'})
        else:
            indicators.append({'name':'MACD', 'verdict':'중립', 'detail':'전환점 관찰 중'})

        if vol_ratio > 1.5:
            if price_change > 0:
                buy_score += 1
                indicators.append({'name':'거래량', 'verdict':'매수', 'detail':f'급증+상승 ({vol_ratio:.1f}x)'})
            else:
                sell_score += 1
                indicators.append({'name':'거래량', 'verdict':'매도', 'detail':f'급증+하락 ({vol_ratio:.1f}x)'})
        else:
            indicators.append({'name':'거래량', 'verdict':'중립', 'detail':f'평균 수준 ({vol_ratio:.1f}x)'})

        if dist_sup < 3:
            buy_score += 1
            indicators.append({'name':'지지/저항', 'verdict':'매수', 'detail':f'지지선 근접 (+{dist_sup:.1f}%)'})
        elif dist_res < 3:
            sell_score += 1
            indicators.append({'name':'지지/저항', 'verdict':'매도', 'detail':f'저항선 근접 (-{dist_res:.1f}%)'})
        else:
            indicators.append({'name':'지지/저항', 'verdict':'중립', 'detail':f'지지 +{dist_sup:.1f}% / 저항 -{dist_res:.1f}%'})

        if buy_score > sell_score + 1:
            verdict = '매수'
        elif sell_score > buy_score + 1:
            verdict = '매도'
        else:
            verdict = '관망'

        confidence = max(buy_score, sell_score) / (buy_score + sell_score + 2) * 100

        v_color = {'매수':'<strong style="color:#00ff88">매수 신호</strong>', '매도':'<strong style="color:#ff3b5c">매도 신호</strong>', '관망':'<strong style="color:#ffb800">관망</strong>'}
        summary = f"<strong>{ticker}</strong> 종목 기술적 분석 결과, 전반적으로 {v_color[verdict]}가 우세합니다 (매수 {buy_score}점 vs 매도 {sell_score}점). "
        summary += f"RSI는 {rsi_val:.1f}로 {'과매도 구간으로 기술적 반등 가능성이 있습니다.' if rsi_val<30 else '과매수 구간으로 단기 조정 가능성이 있습니다.' if rsi_val>70 else '중립 구간입니다.'} "
        summary += f"{'단기 이동평균이 중장기선을 상회하며 상승 모멘텀을 보입니다.' if ma5_val>ma20_val else '단기 이동평균이 중장기선을 하회하며 하락 압력이 있습니다.'} "
        summary += f"볼린저밴드 내 위치는 {bb_pos:.0f}%이며, 거래량은 평균 대비 {vol_ratio:.1f}배 수준입니다."

        def safe_list(s):
            return [None if (v is None or (isinstance(v, float) and np.isnan(v))) else round(float(v), 4) for v in s]

        return jsonify({
            'ticker': ticker,
            'name': name,
            'current': current,
            'price_fmt': price_fmt,
            'price_change': price_change,
            'verdict': verdict,
            'buy_score': buy_score,
            'sell_score': sell_score,
            'confidence': confidence,
            'indicators': indicators,
            'summary': summary,
            'dates': dates,
            'prices': safe_list(closes),
            'ma5': safe_list(ma5),
            'ma20': safe_list(ma20),
            'bb_upper': safe_list(bb_upper),
            'bb_lower': safe_list(bb_lower),
        })

    except Exception as e:
        return jsonify({'error': f'분석 중 오류 발생: {str(e)}'})

@app.route('/news')
def get_news():
    ticker = request.args.get('ticker', '').upper()
    if not ticker or not FINNHUB_KEY:
        return jsonify({'news': []})
    try:
        today = datetime.datetime.now().strftime('%Y-%m-%d')
        month_ago = (datetime.datetime.now() - datetime.timedelta(days=30)).strftime('%Y-%m-%d')
        url = f"https://finnhub.io/api/v1/company-news?symbol={ticker}&from={month_ago}&to={today}&token={FINNHUB_KEY}"
        r = requests.get(url, timeout=10)
        news = r.json()
        result = []
        for item in news[:8]:
            title = item.get('headline', '')
            link = item.get('url', '')
            pub = item.get('datetime', 0)
            publisher = item.get('source', '')
            date_str = datetime.datetime.fromtimestamp(pub).strftime('%Y-%m-%d') if pub else ''

            bad_keywords = ['하락','급락','손실','적자','위기','악재','소송','제재','리콜','경고','하향','매도','우려','둔화','감소','부진']
            good_keywords = ['상승','급등','호재','실적','흑자','성장','신고가','매수','상향','확대','증가','호조','계약','협약','개발','출시']
            bad_en = ['fall','drop','decline','loss','lawsuit','recall','warning','downgrade','sell','concern','slow','cut','weak','plunge','slump']
            good_en = ['rise','surge','gain','profit','growth','high','buy','upgrade','expand','record','deal','launch','beat','soar','jump']

            sentiment = '중립'
            for kw in bad_keywords:
                if kw in title:
                    sentiment = '악재'
                    break
            if sentiment == '중립':
                for kw in good_keywords:
                    if kw in title:
                        sentiment = '호재'
                        break
            title_lower = title.lower()
            if sentiment == '중립':
                for kw in bad_en:
                    if kw in title_lower:
                        sentiment = '악재'
                        break
            if sentiment == '중립':
                for kw in good_en:
                    if kw in title_lower:
                        sentiment = '호재'
                        break

            if title:
                result.append({'title': title, 'link': link, 'date': date_str, 'publisher': publisher, 'sentiment': sentiment})
        return jsonify({'news': result})
    except Exception as e:
        return jsonify({'news': [], 'error': str(e)})

if __name__ == '__main__':
    print("=" * 50)
    print("  STOCKSCAN 실행 중...")
    print("  브라우저에서 http://localhost:5000 접속!")
    print("=" * 50)
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
