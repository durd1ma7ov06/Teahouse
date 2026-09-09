// Teahouse Telegram Mini App Logic

// Telegram WebApp SDK Initialization
const tg = window.Telegram?.WebApp;
if (tg) {
  try {
    tg.ready();
    tg.expand();
  } catch (e) {
    console.log("TG WebApp init:", e);
  }
}

// Global State
const appState = {
  currentTab: 'overview',
  formStep: 1,
  formData: {
    telegram_id: tg?.initDataUnsafe?.user?.id || 10001,
    username: tg?.initDataUnsafe?.user?.username || '',
    full_name: [tg?.initDataUnsafe?.user?.first_name, tg?.initDataUnsafe?.user?.last_name].filter(Boolean).join(' ') || '',
    phone: '',
    role: '',
    company: '',
    industry: 'Axborot texnologiyalari (IT)',
    seniority: 'O\'rta mutaxassis',
    experience_years: 4,
    age: 27,
    target_partner: 'Biznes hamkor / Hammuassis',
    target_industry: 'Barcha sohalar',
    can_offer: '',
    interests: '',
    bio_summary: ''
  }
};

// DOM Elements
document.addEventListener('DOMContentLoaded', () => {
  initTabs();
  initTableSimulator();
  initCountdown();
  initFormInteractions();
  prefillUser();
});

function triggerHaptic(type = 'light') {
  if (tg?.HapticFeedback) {
    try {
      tg.HapticFeedback.impactOccurred(type);
    } catch (e) {}
  }
}

function showToast(message) {
  const toast = document.getElementById('toast-message');
  if (!toast) return;
  toast.textContent = message;
  toast.classList.add('show');
  setTimeout(() => {
    toast.classList.remove('show');
  }, 2500);
}

// Prefill user from Telegram
function prefillUser() {
  if (appState.formData.full_name) {
    const nameInput = document.getElementById('input-full-name');
    if (nameInput && !nameInput.value) {
      nameInput.value = appState.formData.full_name;
    }
  }
}

// Tab Navigation
function initTabs() {
  const tabBtns = document.querySelectorAll('.nav-tab-btn');
  tabBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      triggerHaptic('light');
      const targetTab = btn.getAttribute('data-tab');
      switchTab(targetTab);
    });
  });
}

function switchTab(tabName) {
  appState.currentTab = tabName;
  
  document.querySelectorAll('.nav-tab-btn').forEach(btn => {
    btn.classList.toggle('active', btn.getAttribute('data-tab') === tabName);
  });
  
  document.querySelectorAll('.tab-content').forEach(content => {
    content.classList.toggle('active', content.id === `tab-${tabName}`);
  });
  
  window.scrollTo({ top: 0, behavior: 'smooth' });
}

// Table Simulator
const seatProfiles = {
  seat1: {
    role: "Startap asoschisi (Siz)",
    detail: "B2B SaaS platforma ustida ishlaydi. 99% moslik: Yangi bozorlarga chiqish va strategik hamkorlar qidirmoqda."
  },
  seat2: {
    role: "Investor / Moliya direktori",
    detail: "Seed va Series A bosqichidagi loyihalarga sarmoya kirituvchi farishta investor. Moliyaviy modellashtirishda yordam beradi."
  },
  seat3: {
    role: "Katta dasturchi (Tech Lead)",
    detail: "Sun'iy intellekt va yuqori yuklamali tizimlar arxitektori. Yangi loyihalar uchun texnologik yechimlar taklif qiladi."
  },
  seat4: {
    role: "Marketing va Growth rahbari",
    detail: "Raqamli savdo va xalqaro auditoriyani jalb qilish bo'yicha mutaxassis. Mijozlar oqimini oshirish bo'yicha tajribaga ega."
  }
};

function initTableSimulator() {
  const seats = document.querySelectorAll('.seat-item');
  const roleElem = document.getElementById('seat-info-role');
  const detailElem = document.getElementById('seat-info-detail');

  seats.forEach(seat => {
    seat.addEventListener('click', () => {
      triggerHaptic('medium');
      seats.forEach(s => s.classList.remove('active'));
      seat.classList.add('active');
      
      const seatKey = seat.getAttribute('data-seat');
      const info = seatProfiles[seatKey];
      if (info && roleElem && detailElem) {
        roleElem.textContent = info.role;
        detailElem.textContent = info.detail;
      }
    });
  });
}

// Countdown to Next Wednesday 20:00 Tashkent time (UTC+5)
function initCountdown() {
  const timerElem = document.getElementById('countdown-display');
  if (!timerElem) return;

  function update() {
    const now = new Date();
    // Tashkent is UTC+5
    const nowUtc = now.getTime() + (now.getTimezoneOffset() * 60000);
    const tashkentTime = new Date(nowUtc + (3600000 * 5));

    // Next Wednesday 20:00
    const target = new Date(tashkentTime);
    const currentDay = tashkentTime.getDay(); // 0: Sun, 3: Wed
    let daysUntilWed = (3 - currentDay + 7) % 7;
    
    target.setDate(tashkentTime.getDate() + daysUntilWed);
    target.setHours(20, 0, 0, 0);

    if (daysUntilWed === 0 && tashkentTime.getHours() >= 20) {
      target.setDate(target.getDate() + 7);
    }

    const diff = target - tashkentTime;
    const days = Math.floor(diff / (1000 * 60 * 60 * 24));
    const hours = Math.floor((diff / (1000 * 60 * 60)) % 24);
    const minutes = Math.floor((diff / 1000 / 60) % 60);
    const seconds = Math.floor((diff / 1000) % 60);

    timerElem.textContent = `${days}k ${hours}s ${minutes}m ${seconds}s`;
  }

  update();
  setInterval(update, 1000);
}

// Two-Stage Form & Step Interactions
function initFormInteractions() {
  // Industry Chips
  document.querySelectorAll('.industry-chip').forEach(chip => {
    chip.addEventListener('click', () => {
      triggerHaptic('light');
      document.querySelectorAll('.industry-chip').forEach(c => c.classList.remove('selected'));
      chip.classList.add('selected');
      appState.formData.industry = chip.getAttribute('data-val');
    });
  });

  // Seniority Cards
  document.querySelectorAll('.seniority-card').forEach(card => {
    card.addEventListener('click', () => {
      triggerHaptic('light');
      document.querySelectorAll('.seniority-card').forEach(c => c.classList.remove('selected'));
      card.classList.add('selected');
      appState.formData.seniority = card.getAttribute('data-val');
      appState.formData.experience_years = parseInt(card.getAttribute('data-years') || '4');
    });
  });

  // Age Chips
  document.querySelectorAll('.age-chip').forEach(chip => {
    chip.addEventListener('click', () => {
      triggerHaptic('light');
      document.querySelectorAll('.age-chip').forEach(c => c.classList.remove('selected'));
      chip.classList.add('selected');
      appState.formData.age = parseInt(chip.getAttribute('data-val') || '28');
    });
  });

  // Partner Goal Chips
  document.querySelectorAll('.goal-chip').forEach(chip => {
    chip.addEventListener('click', () => {
      triggerHaptic('light');
      document.querySelectorAll('.goal-chip').forEach(c => c.classList.remove('selected'));
      chip.classList.add('selected');
      appState.formData.target_partner = chip.getAttribute('data-val');
    });
  });

  // Target Industry Chips
  document.querySelectorAll('.target-ind-chip').forEach(chip => {
    chip.addEventListener('click', () => {
      triggerHaptic('light');
      document.querySelectorAll('.target-ind-chip').forEach(c => c.classList.remove('selected'));
      chip.classList.add('selected');
      appState.formData.target_industry = chip.getAttribute('data-val');
    });
  });

  // Next / Prev Step Buttons
  const btnNextStage1 = document.getElementById('btn-next-stage1');
  if (btnNextStage1) {
    btnNextStage1.addEventListener('click', () => {
      triggerHaptic('medium');
      validateAndGoStage2();
    });
  }

  const btnPrevStage1 = document.getElementById('btn-prev-stage1');
  if (btnPrevStage1) {
    btnPrevStage1.addEventListener('click', () => {
      triggerHaptic('light');
      goToStep(1);
    });
  }

  const btnSubmitForm = document.getElementById('btn-submit-form');
  if (btnSubmitForm) {
    btnSubmitForm.addEventListener('click', () => {
      triggerHaptic('heavy');
      validateAndFinishForm();
    });
  }
}

function goToStep(step) {
  appState.formStep = step;

  // Update progress nodes
  document.querySelectorAll('.step-node').forEach(node => {
    const nodeStep = parseInt(node.getAttribute('data-step'));
    node.classList.toggle('active', nodeStep === step);
    node.classList.toggle('completed', nodeStep < step);
  });

  const progressElem = document.querySelector('.step-indicator-progress');
  if (progressElem) {
    if (step === 1) progressElem.style.width = '0%';
    if (step === 2) progressElem.style.width = '50%';
    if (step === 3) progressElem.style.width = '100%';
  }

  // Show corresponding step container
  document.getElementById('form-step-1').style.display = (step === 1) ? 'block' : 'none';
  document.getElementById('form-step-2').style.display = (step === 2) ? 'block' : 'none';
  document.getElementById('form-step-3').style.display = (step === 3) ? 'block' : 'none';

  window.scrollTo({ top: 0, behavior: 'smooth' });
}

function validateAndGoStage2() {
  const nameVal = document.getElementById('input-full-name')?.value.trim();
  const phoneVal = document.getElementById('input-phone')?.value.trim();
  const roleVal = document.getElementById('input-role')?.value.trim();
  const companyVal = document.getElementById('input-company')?.value.trim();

  if (!nameVal) {
    showToast("Iltimos, ism va familiyangizni kiriting.");
    document.getElementById('input-full-name')?.focus();
    return;
  }

  if (!phoneVal || phoneVal.length < 9) {
    showToast("Iltimos, telefon raqamingizni to'liq kiriting.");
    document.getElementById('input-phone')?.focus();
    return;
  }

  if (!roleVal) {
    showToast("Iltimos, kasb yoki lavozimingizni kiriting.");
    document.getElementById('input-role')?.focus();
    return;
  }

  appState.formData.full_name = nameVal;
  appState.formData.phone = phoneVal;
  appState.formData.role = roleVal;
  appState.formData.company = companyVal || 'Mustaqil loyiha';

  goToStep(2);
}

function validateAndFinishForm() {
  const offerVal = document.getElementById('input-offer')?.value.trim();
  const interestsVal = document.getElementById('input-interests')?.value.trim();

  appState.formData.can_offer = offerVal || 'Professional bilim va hamkorlik';
  appState.formData.interests = interestsVal || 'Biznes va texnologiyalar';

  // Render VIP Pass
  renderVipPass();

  // Save via API
  saveProfileToBackend();

  goToStep(3);
}

function renderVipPass() {
  const d = appState.formData;
  document.getElementById('pass-name').textContent = d.full_name;
  document.getElementById('pass-role').textContent = `${d.role} @ ${d.company}`;
  document.getElementById('pass-industry').textContent = d.industry;
  document.getElementById('pass-seniority').textContent = `${d.seniority} (${d.experience_years} yil)`;
  document.getElementById('pass-target').textContent = d.target_partner;
  document.getElementById('pass-target-ind').textContent = d.target_industry;
  document.getElementById('pass-id').textContent = `TH-${Math.abs(d.telegram_id % 90000) + 10000}`;
}

async function saveProfileToBackend() {
  try {
    const payload = {
      telegram_id: appState.formData.telegram_id,
      full_name: appState.formData.full_name,
      phone: appState.formData.phone,
      role: appState.formData.role,
      company: appState.formData.company,
      industry: appState.formData.industry,
      seniority: appState.formData.seniority,
      experience_years: appState.formData.experience_years,
      age: appState.formData.age,
      target_partner: appState.formData.target_partner,
      target_industry: appState.formData.target_industry,
      can_offer: appState.formData.can_offer,
      interests: appState.formData.interests
    };

    const res = await fetch('/api/profile', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    if (res.ok) {
      showToast("Profilingiz muvaffaqiyatli saqlandi!");
      if (tg?.sendData) {
        tg.sendData(JSON.stringify({ action: "profile_updated", ...payload }));
      }
    }
  } catch (err) {
    console.error("Save profile error:", err);
  }
}
