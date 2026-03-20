/* ============================================================
   HealVN — main.js
   ============================================================ */

/* ---------- Scroll animations ---------- */
const observer = new IntersectionObserver(
  (entries) => entries.forEach(e => {
    if (e.isIntersecting) { e.target.classList.add('visible'); }
  }),
  { threshold: 0.12 }
);
document.querySelectorAll('.fade-up, .scale-in').forEach(el => observer.observe(el));

/* ---------- Mobile menu ---------- */
const hamburger = document.getElementById('hamburger');
const mobileMenu = document.getElementById('mobileMenu');
if (hamburger && mobileMenu) {
  hamburger.addEventListener('click', () => mobileMenu.classList.toggle('open'));
  document.addEventListener('click', e => {
    if (!hamburger.contains(e.target) && !mobileMenu.contains(e.target))
      mobileMenu.classList.remove('open');
  });
}

/* ---------- AI Chat Widget ---------- */
const AI_RESPONSES = {
  default: [
    "Chào bạn! Mình là Hana — AI Wellness Advisor của HealVN. 🌿 Bạn muốn tìm loại wellness nào? Ví dụ: nghỉ dưỡng biển, thiền định núi, hay detox?",
    "Dựa trên profile của bạn, mình gợi ý **Phú Quốc Wellness Retreat** — kết hợp yoga bình minh + liệu pháp nước biển. Thời gian lý tưởng: 5–7 ngày. 🌊",
    "Ngân sách của bạn khoảng bao nhiêu? Mình có các gói từ **$500/người/tuần** đến premium **$3,000/tuần** tại resort 5 sao.",
    "Tuyệt! Mình sẽ tạo **Wellness Journey** riêng cho bạn. Bao gồm: lịch trình ngày-giờ, gói ăn organic, và kết nối therapist địa phương. ✨",
    "Bạn có muốn mình so sánh 3 retreat phù hợp nhất với bạn không? Mình đang phân tích 1,200+ retreat verified trên HealVN... 🤖"
  ],
  "phú quốc": [
    "🌴 Phú Quốc — thiên đường wellness hàng đầu VN! Mình có 47 retreat verified tại đây. Nổi bật: An Lam Retreats Ninh Van Bay, Fusion Resort & Villas, Six Senses Phu Quoc. Rating trung bình: 4.8/5. Bookng nhiều nhất tháng 3–5 & 9–11.",
  ],
  "hà giang": [
    "🏔️ Hà Giang — perfect cho forest bathing & cultural immersion! Mình gợi ý Đồng Văn Eco Retreat hoặc homestay trekking với người Mông. Thời tiết tốt nhất: tháng 10–12. Budget-friendly: từ $200/tuần.",
  ],
  "đà lạt": [
    "🌸 Đà Lạt — thành phố của thiền định và hoa! Nhiệt độ mát mẻ quanh năm, rất phù hợp yoga retreat + art therapy. Top pick: La Sapinette Boutique Hotel Retreat. 4.9⭐",
  ],
  "budget": [
    "💚 Mình có nhiều lựa chọn budget-friendly: Gói Economy ($300–500/tuần) — bao gồm yoga sáng tối, ăn organic × 3 bữa, accommodation cơ bản. Checkout retreat tại Mộc Châu hoặc Bình Ba!",
  ]
};

let chatInitialized = false;
function initChat() {
  const msgContainer = document.getElementById('chatMessages');
  const input = document.getElementById('chatInput');
  const sendBtn = document.getElementById('sendBtn');
  if (!msgContainer || !input || !sendBtn) return;
  if (chatInitialized) return;
  chatInitialized = true;

  function addMessage(text, isUser = false) {
    const div = document.createElement('div');
    div.className = `msg ${isUser ? 'user' : 'bot'}`;
    const avatar = isUser ? '' : `<div class="ai-avatar" style="width:32px;height:32px;font-size:0.9rem">🌿</div>`;
    div.innerHTML = `${avatar}<div class="msg-bubble">${text}</div>`;
    msgContainer.appendChild(div);
    msgContainer.scrollTop = msgContainer.scrollHeight;
    return div;
  }

  function showTyping() {
    const div = document.createElement('div');
    div.className = 'msg bot';
    div.id = 'typingIndicator';
    div.innerHTML = `<div class="ai-avatar" style="width:32px;height:32px;font-size:0.9rem">🌿</div>
      <div class="msg-bubble"><div class="typing-indicator"><span></span><span></span><span></span></div></div>`;
    msgContainer.appendChild(div);
    msgContainer.scrollTop = msgContainer.scrollHeight;
  }

  function removeTyping() {
    const t = document.getElementById('typingIndicator');
    if (t) t.remove();
  }

  function getBotReply(msg) {
    const lower = msg.toLowerCase();
    for (const key of Object.keys(AI_RESPONSES)) {
      if (key !== 'default' && lower.includes(key)) {
        return AI_RESPONSES[key][0];
      }
    }
    if (lower.includes('giá') || lower.includes('budget') || lower.includes('tiền')) return AI_RESPONSES['budget'][0];
    const defaults = AI_RESPONSES['default'];
    return defaults[Math.floor(Math.random() * defaults.length)];
  }

  function sendMessage() {
    const text = input.value.trim();
    if (!text) return;
    addMessage(text, true);
    input.value = '';
    showTyping();
    setTimeout(() => {
      removeTyping();
      addMessage(getBotReply(text));
    }, 1400);
  }

  sendBtn.addEventListener('click', sendMessage);
  input.addEventListener('keydown', e => { if (e.key === 'Enter') sendMessage(); });
}

/* ---------- Pill nav filter ---------- */
function initPillNav() {
  document.querySelectorAll('.pill-nav').forEach(nav => {
    nav.querySelectorAll('.pill-nav-item').forEach(item => {
      item.addEventListener('click', () => {
        nav.querySelectorAll('.pill-nav-item').forEach(i => i.classList.remove('active'));
        item.classList.add('active');
        const target = item.dataset.target;
        if (target) filterCards(target);
      });
    });
  });
}

function filterCards(category) {
  document.querySelectorAll('[data-category]').forEach(card => {
    if (category === 'all' || card.dataset.category === category) {
      card.style.display = '';
      card.style.opacity = '0';
      card.style.transform = 'translateY(16px)';
      setTimeout(() => { card.style.transition = 'all 0.4s ease'; card.style.opacity = '1'; card.style.transform = 'translateY(0)'; }, 50);
    } else {
      card.style.display = 'none';
    }
  });
}

/* ---------- Progress bar animation ---------- */
function animateProgressBars() {
  document.querySelectorAll('.progress-fill').forEach(bar => {
    const width = bar.dataset.width || '0%';
    bar.style.width = '0%';
    setTimeout(() => { bar.style.width = width; }, 300);
  });
}

/* ---------- Counter animation ---------- */
function animateCounter(el, target, suffix = '', duration = 1800) {
  let start = 0;
  const step = target / (duration / 16);
  const timer = setInterval(() => {
    start = Math.min(start + step, target);
    el.textContent = Math.floor(start).toLocaleString() + suffix;
    if (start >= target) clearInterval(timer);
  }, 16);
}

function initCounters() {
  document.querySelectorAll('[data-counter]').forEach(el => {
    const io = new IntersectionObserver(entries => {
      if (entries[0].isIntersecting) {
        const val = parseFloat(el.dataset.counter);
        const suffix = el.dataset.suffix || '';
        animateCounter(el, val, suffix);
        io.disconnect();
      }
    });
    io.observe(el);
  });
}

/* ---------- Search bar ---------- */
function initSearch() {
  const search = document.getElementById('retreatSearch');
  if (!search) return;
  search.addEventListener('input', () => {
    const q = search.value.toLowerCase();
    document.querySelectorAll('.retreat-card').forEach(card => {
      const text = card.textContent.toLowerCase();
      card.style.display = text.includes(q) ? '' : 'none';
    });
  });
}

/* ---------- Smooth active nav link ---------- */
function highlightNav() {
  const links = document.querySelectorAll('.nav-links a');
  const path = location.pathname.split('/').pop() || 'index.html';
  links.forEach(a => {
    const href = a.getAttribute('href');
    if (href === path || (path === 'index.html' && href === '#home')) {
      a.style.color = 'var(--clr-jade)';
    }
  });
}

/* ---------- Init ---------- */
document.addEventListener('DOMContentLoaded', () => {
  initChat();
  initPillNav();
  initCounters();
  animateProgressBars();
  initSearch();
  highlightNav();
});
