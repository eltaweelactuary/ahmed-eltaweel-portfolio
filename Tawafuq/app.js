import { CONFIG } from './config.js';

document.addEventListener('DOMContentLoaded', () => {
    // --- State Management ---
    let profiles = [];
    let currentStep = 1;

    // --- DOM Elements ---
    const profilesContainer = document.getElementById('featuredProfiles');
    const modal = document.getElementById('registrationModal');
    const form = document.getElementById('tawafuqForm');
    const progressBar = document.getElementById('progressBar');
    const steps = document.querySelectorAll('.form-step');
    const nextBtn = document.getElementById('nextBtn');
    const prevBtn = document.getElementById('prevBtn');
    const submitBtn = document.getElementById('submitBtn');
    const successMsg = document.getElementById('formSuccess');

    // --- Modal Logic ---
    const openModal = () => {
        modal.style.display = 'flex';
        document.body.style.overflow = 'hidden'; // prevent scroll
    };

    const closeModal = () => {
        modal.style.display = 'none';
        document.body.style.overflow = 'auto';
        resetForm();
    };

    const resetForm = () => {
        currentStep = 1;
        form.reset();
        form.style.display = 'block';
        successMsg.style.display = 'none';
        updateStep();
    };

    // Close on overlay click
    modal.addEventListener('click', (e) => {
        if (e.target === modal) closeModal();
    });

    document.querySelectorAll('.close-modal').forEach(btn => {
        btn.addEventListener('click', closeModal);
    });

    // --- Wire up register buttons ---
    const wireRegisterButtons = () => {
        document.querySelectorAll('.open-register-btn').forEach(el => {
            el.onclick = (e) => {
                e.preventDefault();
                openModal();
            };
        });
    };

    wireRegisterButtons();

    // --- Navigation Logic ---
    const updateStep = () => {
        steps.forEach(step => step.classList.remove('active'));
        document.querySelector(`.form-step[data-step="${currentStep}"]`).classList.add('active');
        
        // Progress bar
        progressBar.style.width = `${(currentStep / 6) * 100}%`;

        // Buttons visibility
        prevBtn.style.display = currentStep === 1 ? 'none' : 'block';
        if (currentStep === 6) {
            nextBtn.style.display = 'none';
            submitBtn.style.display = 'block';
        } else {
            nextBtn.style.display = 'block';
            submitBtn.style.display = 'none';
        }
    };

    nextBtn.onclick = () => {
        if (validateStep()) {
            if (window.tracker) {
                tracker.event('tawafuq_step_complete', { 
                    step: currentStep,
                    next_step: currentStep + 1 
                });
            }
            currentStep++;
            updateStep();
            modal.scrollTo(0, 0);
        }
    };

    prevBtn.onclick = () => {
        currentStep--;
        updateStep();
        modal.scrollTo(0, 0);
    };

    const validateStep = () => {
        const activeStep = document.querySelector(`.form-step[data-step="${currentStep}"]`);
        const inputs = activeStep.querySelectorAll('[required]');
        let valid = true;
        
        inputs.forEach(input => {
            if (!input.value) {
                input.style.borderColor = 'red';
                valid = false;
            } else {
                input.style.borderColor = 'rgba(255, 255, 255, 0.2)';
            }
        });

        if (!valid) alert('يرجى ملء كافة الحقول المطلوبة (*) المتبقية في هذه الخطوة');
        return valid;
    };

    // --- Conditional Logic ---
    const setupConditional = (triggerId, targetId, valueToShow) => {
        const trigger = document.getElementById(triggerId);
        const target = document.getElementById(targetId);
        if (!trigger || !target) return;
        
        trigger.onchange = () => {
            target.style.display = trigger.value === valueToShow ? 'block' : 'none';
        };
    };

    setupConditional('maritalStatus', 'polygamyDetails', 'متزوج');
    setupConditional('isExpat', 'expatDetails', 'نعم');
    setupConditional('hasHealthIssues', 'healthDetails', 'نعم');

    // --- Submit Logic ---
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        console.log('Submit event triggered');
        
        if (CONFIG.googleScriptUrl.includes('REPLACE')) {
            alert('يرجى ضبط رابط الـ Script أولاً في ملف config.js');
            return;
        }

        if (submitBtn.disabled) return;

        submitBtn.disabled = true;
        submitBtn.innerText = 'جاري الإرسال...';

        const formData = new FormData(form);
        const data = Object.fromEntries(formData.entries());
        
        // Handle File properly for GAS using FileReader (Base64)
        const photoFile = formData.get('photo');
        if (photoFile && photoFile.size > 0) {
            console.log('Processing photo...');
            const reader = new FileReader();
            reader.readAsDataURL(photoFile);
            reader.onload = async () => {
                data.photoData = reader.result.split(',')[1];
                data.photoType = photoFile.type;
                data.photoName = photoFile.name;
                await sendToGas(data);
            };
            reader.onerror = () => {
                console.error('Photo read error');
                sendToGas(data); 
            };
        } else {
            await sendToGas(data);
        }
    });

    const sendToGas = async (data) => {
        console.log('--- Initiating Submission ---');
        console.log('Target URL:', CONFIG.googleScriptUrl);
        
        try {
            // IMPORTANT: With 'no-cors', we must use a 'simple' content-type.
            // application/json is NOT allowed in no-cors. text/plain is safe.
            await fetch(CONFIG.googleScriptUrl, {
                method: 'POST',
                mode: 'no-cors', 
                cache: 'no-cache',
                headers: { 'Content-Type': 'text/plain' },
                body: JSON.stringify(data)
            });
            
            console.log('Submission sent successfully (Opaque result).');
            
            if (window.tracker) {
                tracker.event('tawafuq_submission_success');
            }

            // Hide form and show success regardless of result content (since it's no-cors)
            form.style.display = 'none';
            successMsg.style.display = 'block';
            modal.scrollTo(0, 0);
            
        } catch (error) {
            console.error('Submission technical error:', error);
            if (window.tracker) {
                tracker.event('tawafuq_submission_error', { error: error.message });
            }
            alert('حدث خطأ فني أثناء الإرسال. يرجى التأكد من اتصال الإنترنت.');
        } finally {
            submitBtn.disabled = false;
            submitBtn.innerText = 'إرسال البيانات';
        }
    };

    // --- Google Sheets Data Rendering ---
    const fetchProfiles = async () => {
        const loadDummyData = () => {
            profiles = [
                { name: 'محمد أ.', age: 28, city: 'القاهرة', job: 'مهندس برمجيات', gender: 'male' },
                { name: 'سارة م.', age: 25, city: 'الإسكندرية', job: 'معلمة', gender: 'female' },
                { name: 'أحمد ف.', age: 31, city: 'دمياط', job: 'طبيب', gender: 'male' }
            ];
            renderProfiles();
        };

        if (!CONFIG.spreadsheetId || CONFIG.spreadsheetId.includes('REPLACE')) {
            loadDummyData();
            return;
        }

        const url = `https://docs.google.com/spreadsheets/d/${CONFIG.spreadsheetId}/gviz/tq?tqx=out:json&tq&gid=${CONFIG.sheetGid}`;
        try {
            const response = await fetch(url);
            if (!response.ok) throw new Error('Sheet not found');
            
            const text = await response.text();
            const jsonStr = text.substring(text.indexOf('{'), text.lastIndexOf('}') + 1);
            const data = JSON.parse(jsonStr);
            
            profiles = data.table.rows.map((row, index) => {
                // Mapping matching the old exact columns (set by google_script.gs V2):
                // 1: Name, 2: Age, 3: City, 4: Job, 5: Gender text
                const name = row.c[1]?.v || '';
                let age = row.c[2]?.v || '';
                const city = row.c[3]?.v || '';
                const job = row.c[4]?.v || '';
                const genderText = (row.c[5]?.v || '').toString();
                
                // If age is missing but DOB is present in column 16
                if (!age) {
                    const dob = row.c[16]?.v || '';
                    if (dob && dob.includes('-')) {
                        const birthYear = parseInt(dob.split('-')[0]);
                        if (!isNaN(birthYear)) age = new Date().getFullYear() - birthYear;
                    }
                }

                return {
                    id: index,
                    name: name,
                    age: age,
                    city: city,
                    job: job,
                    gender: genderText.includes('شاب') ? 'male' : 'female',
                };
            }).filter(p => p.name && p.name !== 'الاسم بالكامل' && p.name !== 'Ko'); // Filter headers and tests
            
            if (profiles.length === 0) loadDummyData();
            else renderProfiles();
        } catch (e) { 
            console.warn('Could not catch live profiles, loading dummy data instead.', e);
            loadDummyData(); 
        }
    };

    const renderProfiles = () => {
        if (!profilesContainer) return;
        profilesContainer.innerHTML = profiles.map(profile => `
            <div class="profile-card">
                <div class="profile-img">
                    <i class="fas fa-user-circle"></i>
                    <span class="profile-badge">${profile.gender === 'male' ? 'شاب' : 'شابة'}</span>
                </div>
                <div class="profile-info">
                    <h3>${profile.name}</h3>
                    <div class="profile-details">
                        <span><i class="fas fa-map-marker-alt"></i> ${profile.city}</span>
                        <span><i class="fas fa-birthday-cake"></i> ${profile.age} عام</span>
                        <span><i class="fas fa-briefcase"></i> ${profile.job}</span>
                    </div>
                    <button class="btn btn-primary btn-full open-register-btn">التسجيل للتواصل</button>
                </div>
            </div>
        `).join('');

        wireRegisterButtons();
    };

    fetchProfiles();
});
