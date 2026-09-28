const messages = document.querySelector('#chat-messages');
const form = document.querySelector('#chat-form');
const input = document.querySelector('#message-input');
const send = document.querySelector('#send-button');
const memoryList = document.querySelector('#memory-list');
const conversationList = document.querySelector('#conversation-list');
const dialog = document.querySelector('#memory-dialog');
let conversationId = null;

const escapeHtml = (value) => value.replace(/[&<>'"]/g, char => ({ '&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#039;','"':'&quot;' }[char]));
const clock = () => new Intl.DateTimeFormat('id-ID', { hour:'2-digit', minute:'2-digit' }).format(new Date());

function addMessage(role, content, typing = false) {
  const article = document.createElement('article');
  article.className = `message ${role}-message${typing ? ' typing' : ''}`;
  article.innerHTML = `<div class="avatar">${role === 'assistant' ? 'P' : 'A'}</div><div><div class="bubble">${escapeHtml(content)}</div><time>${typing ? '' : clock()}</time></div>`;
  messages.append(article); messages.scrollTop = messages.scrollHeight;
  return article;
}
function resetChat() { conversationId = null; messages.innerHTML = ''; addMessage('assistant', 'Halo, saya PISCA. Ada yang bisa saya bantu?'); }
function autoGrow() { input.style.height = 'auto'; input.style.height = `${Math.min(input.scrollHeight, 150)}px`; }

async function request(url, options = {}) {
  const response = await fetch(url, { headers: { 'Content-Type':'application/json' }, ...options });
  if (response.status === 204) return null;
  const data = await response.json();
  if (!response.ok) throw new Error(data.detail || 'Terjadi kesalahan pada server.');
  return data;
}
async function loadMemories() {
  const items = await request('/api/memories');
  memoryList.innerHTML = items.length ? '' : '<p class="empty-state">Belum ada memory.</p>';
  items.forEach(item => {
    const card = document.createElement('article'); card.className = 'memory-card';
    card.innerHTML = `<header><div><strong>${escapeHtml(item.key)}</strong><br><small>${escapeHtml(item.category)}</small></div><div class="memory-actions"><button class="delete-mini" aria-label="Edit">✎</button><button class="delete-mini" aria-label="Hapus">×</button></div></header><p>${escapeHtml(item.value)}</p>`;
    card.querySelectorAll('button')[0].onclick = () => openMemory(item);
    card.querySelectorAll('button')[1].onclick = async () => { if (confirm(`Hapus memory "${item.key}"?`)) { await request(`/api/memories/${item.id}`, { method:'DELETE' }); loadMemories(); }};
    memoryList.append(card);
  });
}
async function loadConversations() {
  const items = await request('/api/conversations');
  conversationList.innerHTML = items.length ? '' : '<p class="empty-state">Belum ada percakapan.</p>';
  items.forEach(item => {
    const row = document.createElement('div'); row.className = 'conversation-item';
    row.innerHTML = `<span>${escapeHtml(item.preview)}</span><button class="delete-mini" aria-label="Hapus percakapan">×</button>`;
    row.querySelector('button').onclick = async event => { event.stopPropagation(); await request(`/api/conversations/${item.id}`, { method:'DELETE' }); if (conversationId === item.id) resetChat(); loadConversations(); };
    conversationList.append(row);
  });
}
function openMemory(item = null) {
  document.querySelector('#memory-dialog-title').textContent = item ? 'Edit memory' : 'Tambah memory';
  document.querySelector('#memory-id').value = item?.id || '';
  document.querySelector('#memory-category').value = item?.category || 'personal';
  document.querySelector('#memory-key').value = item?.key || '';
  document.querySelector('#memory-value').value = item?.value || '';
  dialog.showModal();
}
form.addEventListener('submit', async event => {
  event.preventDefault(); const text = input.value.trim(); if (!text) return;
  addMessage('user', text); input.value = ''; autoGrow(); send.disabled = true;
  const loading = addMessage('assistant', 'PISCA sedang berpikir...', true);
  try { const data = await request('/api/chat', { method:'POST', body:JSON.stringify({ message:text, conversation_id:conversationId }) }); conversationId = data.conversation_id; loading.remove(); addMessage('assistant', data.answer); await Promise.all([loadMemories(), loadConversations()]); }
  catch (error) { loading.remove(); addMessage('assistant', error.message); }
  finally { send.disabled = false; input.focus(); }
});
input.addEventListener('input', autoGrow);
input.addEventListener('keydown', event => { if (event.key === 'Enter' && !event.shiftKey) { event.preventDefault(); form.requestSubmit(); } });
document.querySelector('#new-chat').onclick = resetChat; document.querySelector('#clear-chat').onclick = resetChat;
document.querySelector('#menu-toggle').onclick = () => document.querySelector('#sidebar').classList.toggle('open');
document.querySelector('#add-memory').onclick = () => openMemory(); document.querySelector('#close-dialog').onclick = () => dialog.close(); document.querySelector('#cancel-memory').onclick = () => dialog.close();
document.querySelector('#memory-form').addEventListener('submit', async event => { event.preventDefault(); const id = document.querySelector('#memory-id').value; const payload = { category:document.querySelector('#memory-category').value.trim(), key:document.querySelector('#memory-key').value.trim(), value:document.querySelector('#memory-value').value.trim() }; try { await request(id ? `/api/memories/${id}` : '/api/memories', { method:id ? 'PUT':'POST', body:JSON.stringify(payload) }); dialog.close(); loadMemories(); } catch (error) { alert(error.message); } });
loadMemories().catch(() => {}); loadConversations().catch(() => {});
