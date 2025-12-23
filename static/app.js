document.addEventListener('DOMContentLoaded', function() {
    const tabs = document.querySelectorAll('.tab');
    const tabContents = document.querySelectorAll('.tab-content');
    const generateBtn = document.getElementById('generateBtn');
    const generateDslBtn = document.getElementById('generateDslBtn');
    const promptInput = document.getElementById('prompt');
    const dslInput = document.getElementById('dslInput');
    const durationInput = document.getElementById('duration');
    const fpsInput = document.getElementById('fps');
    const modelSelect = document.getElementById('model');
    const videoContainer = document.getElementById('videoContainer');
    const loading = document.getElementById('loading');
    const errorDiv = document.getElementById('error');
    const dslPreview = document.getElementById('dslPreview');
    
    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            tabs.forEach(t => t.classList.remove('active'));
            tabContents.forEach(c => c.classList.remove('active'));
            
            tab.classList.add('active');
            document.getElementById(tab.dataset.tab).classList.add('active');
        });
    });
    
    generateBtn.addEventListener('click', generateFromPrompt);
    generateDslBtn.addEventListener('click', generateFromDsl);
    
    promptInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && e.ctrlKey) {
            generateFromPrompt();
        }
    });
    
    async function generateFromPrompt() {
        const prompt = promptInput.value.trim();
        if (!prompt) {
            showError('Please enter a prompt');
            return;
        }
        
        const duration = parseFloat(durationInput.value) || 3;
        const fps = parseInt(fpsInput.value) || 24;
        const model = modelSelect.value;
        
        showLoading();
        hideError();
        
        try {
            const response = await fetch('/generate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    prompt: prompt,
                    duration: duration,
                    fps: fps,
                    model: model
                })
            });
            
            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.detail || 'Generation failed');
            }
            
            if (data.ok && data.video_base64) {
                displayVideo(data.video_base64);
                if (data.dsl) {
                    dslPreview.textContent = data.dsl;
                    dslPreview.style.display = 'block';
                }
            } else {
                throw new Error(data.error || 'Unknown error');
            }
        } catch (err) {
            showError(err.message);
        } finally {
            hideLoading();
        }
    }
    
    async function generateFromDsl() {
        const dsl = dslInput.value.trim();
        if (!dsl) {
            showError('Please enter DSL code');
            return;
        }
        
        showLoading();
        hideError();
        
        try {
            const response = await fetch('/generate-dsl', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    dsl: dsl
                })
            });
            
            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.detail || 'Generation failed');
            }
            
            if (data.ok && data.video_base64) {
                displayVideo(data.video_base64);
            } else {
                throw new Error(data.error || 'Unknown error');
            }
        } catch (err) {
            showError(err.message);
        } finally {
            hideLoading();
        }
    }
    
    function displayVideo(base64) {
        videoContainer.innerHTML = `
            <video controls autoplay loop>
                <source src="data:video/mp4;base64,${base64}" type="video/mp4">
                Your browser does not support video playback.
            </video>
        `;
    }
    
    function showLoading() {
        loading.classList.add('active');
        generateBtn.disabled = true;
        generateDslBtn.disabled = true;
    }
    
    function hideLoading() {
        loading.classList.remove('active');
        generateBtn.disabled = false;
        generateDslBtn.disabled = false;
    }
    
    function showError(message) {
        errorDiv.textContent = message;
        errorDiv.classList.add('active');
    }
    
    function hideError() {
        errorDiv.classList.remove('active');
    }
    
    async function loadModels() {
        try {
            const response = await fetch('/models');
            const data = await response.json();
            
            let optionsHtml = '<option value="auto">Auto (Best Available)</option>';
            
            if (data.groq) {
                optionsHtml += '<option value="groq">Llama 4 Maverick (Groq)</option>';
            }
            if (data.openai) {
                optionsHtml += '<option value="openai">GPT-4o (OpenAI)</option>';
            }
            optionsHtml += '<option value="fallback">Template (Offline)</option>';
            
            modelSelect.innerHTML = optionsHtml;
            modelSelect.value = 'auto';
            
            updateStatusBar(data);
        } catch (err) {
            console.error('Failed to load models:', err);
            modelSelect.value = 'fallback';
        }
    }
    
    function updateStatusBar(models) {
        const groqDot = document.getElementById('groqStatus');
        const openaiDot = document.getElementById('openaiStatus');
        
        if (groqDot) {
            groqDot.classList.toggle('inactive', !models.groq);
        }
        if (openaiDot) {
            openaiDot.classList.toggle('inactive', !models.openai);
        }
    }
    
    loadModels();
    
    const exampleDsl = `BACKGROUND #1a1a2e
FPS 24
DURATION 3
SHAPE CIRCLE ID ball AT 50,180 RADIUS 30 COLOR #FF4444 MOVE TO 550,180 DUR 3 EASE linear
TEXT "Hello World" AT 220,50 SIZE 36 COLOR #FFFFFF`;
    
    dslInput.placeholder = exampleDsl;
});
