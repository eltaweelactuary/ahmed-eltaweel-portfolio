document.addEventListener('DOMContentLoaded', () => {
    const taxForm = document.getElementById('taxForm');
    const inputs = taxForm.querySelectorAll('input, select, textarea');
    const missingFieldsList = document.getElementById('missingFieldsList');
    const assistantMessage = document.getElementById('assistantMessage');
    const amlAlert = document.getElementById('amlAlert');
    const successScreen = document.getElementById('successScreen');
    const mainContent = document.getElementById('mainContent');

    // قائمة سوداء وهمية للتمثيل
    const amlBlacklist = ["Blacklisted Entity", "Entity X", "فلان الفلاني المحظور"];

    const fileUpload = document.getElementById('fileUpload');
    const fileNameDisplay = document.getElementById('fileNameDisplay');
    const parseFileBtn = document.getElementById('parseFileBtn');

    // محاكاة استجابات Gemini لذراع "أستاذ بيومي"
    const bayoumiQuotes = [
        "يا فندم، الضرايب حق الدولة، خلينا نملى البيانات صح عشان نتجنب الغرامات.",
        "خد بالك، الرقم الضريبي ده هو عنوانك في المصلحة، لازم يكون مظبوط.",
        "أنا هنا عشان أسهلك الدنيا، مصلحة الضرائب دلوقتي بقت رقمية بالكامل.",
        "المستندات اللي رفعتها دي كويسة، بس لازم تفرغ بياناتها صح في الخانات."
    ];

    // قاعدة بيانات المحتالين (نسخة تجريبية)
    const fraudDatabase = [
        { name: "Blacklisted Entity", taxId: "999-999-999", reason: "غسيل أموال" },
        { name: "علي بابا", taxId: "000-000-000", reason: "تهرب ضريبي متكرر" },
        { name: "فلان الفلاني المحظور", taxId: "111-222-333", reason: "قائمة الحظر الدولية" }
    ];

    const fieldLabels = {
        'fullName': 'الاسم الكامل للممول',
        'taxId': 'الرقم الضريبي',
        'transactionType': 'نوع المعاملة',
        'amount': 'قيمة المعاملة (بالجنيه)'
    };

    function updateAssistant() {
        let missing = [];
        let fraudReason = null;

        const currentName = document.getElementById('fullName').value.trim();
        const currentTaxId = document.getElementById('taxId').value.trim();

        // فحص قاعدة بيانات الغش
        const fraudEntry = fraudDatabase.find(entry =>
            (currentName && entry.name.includes(currentName)) ||
            (currentTaxId && entry.taxId === currentTaxId)
        );

        if (fraudEntry) {
            fraudReason = fraudEntry.reason;
        }

        inputs.forEach(input => {
            if (!input.value && fieldLabels[input.id]) {
                missing.push(fieldLabels[input.id]);
            }
        });

        // فحص الملف المرفوع - تم إزالة هذا الشرط من هنا لأنه سيتم التعامل معه بشكل مختلف مع زر التفريغ
        // if (!fileUpload.files.length) {
        //     missing.push("المستندات الداعمة (إلزامي للتدقيق)");
        // }

        // تحديث واجهة بيومي
        missingFieldsList.innerHTML = '';
        if (fraudReason) {
            assistantMessage.innerHTML = `<span style="color: var(--danger)">حاسب يا فندم! فيه مشكلة أمنية هنا...</span>`;
        } else if (missing.length > 0) {
            const quote = bayoumiQuotes[Math.floor(Math.random() * bayoumiQuotes.length)];
            assistantMessage.innerText = `أستاذ بيومي بيقولك: "${quote}"\n\nباقي لنا شوية حاجات عشان نكمل:`;
            missing.forEach(field => {
                const li = document.createElement('li');
                li.innerText = field;
                missingFieldsList.appendChild(li);
            });
        } else {
            assistantMessage.innerText = 'الله ينور! البيانات كده مظبوطة ومطابقة للنموذج. اتفضل قدم بالسلامة.';
        }

        // تنبيه الغش والـ AML
        if (fraudReason) {
            amlAlert.innerHTML = `⚠️ <strong>تنبيه من أستاذ بيومي:</strong> البيانات دي فيها شبهة (${fraudReason}). لازم تراجع مصلحة الضرائب بنفسك فوراً.`;
            amlAlert.style.display = 'block';
        } else {
            amlAlert.style.display = 'none';
        }
    }

    // محاكاة تفريغ البيانات من الملف (Gemini AI Simulation)
    parseFileBtn.addEventListener('click', () => {
        assistantMessage.innerText = 'أستاذ بيومي بيراجع القالب المرفق وبيربطه بالبيانات الرسمية... ثواني يا فندم...';

        setTimeout(() => {
            // محاكاة استخراج البيانات بناءً على القالب الموفر (transaction_template.md)
            document.getElementById('fullName').value = "محمد أحمد السيد علي"; // مثال لاسم رباعي
            document.getElementById('taxId').value = "123-456-789"; // مثال مطابق للتنسيق
            document.getElementById('transactionType').value = "commercial"; // تجاري
            document.getElementById('amount').value = "5000"; // القيمة الموجودة في مثال "طريقة المليء"
            document.getElementById('notes').value = "تم استخراج البيانات آلياً من قالب (transaction_template.md) بواسطة ذكاء أستاذ بيومي. يرجى المراجعة والضغط على التقديم.";

            updateAssistant();
            alert('تم تفريغ البيانات من الملف بنجاح! أستاذ بيومي قام بمطابقة البيانات مع النموذج الرسمي.');
        }, 1500);
    });

    // التعامل مع رفع الملفات
    fileUpload.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            fileNameDisplay.innerText = e.target.files[0].name;
            fileNameDisplay.style.color = '#27ae60';
            parseFileBtn.style.display = 'block';
        } else {
            fileNameDisplay.innerText = 'لم يتم اختيار ملف';
            fileNameDisplay.style.color = '#6c757d';
            parseFileBtn.style.display = 'none';
        }
        updateAssistant();
    });

    // مراقبة التغييرات في الحقول
    inputs.forEach(input => {
        input.addEventListener('input', updateAssistant);
        input.addEventListener('change', updateAssistant);
    });

    taxForm.addEventListener('submit', (e) => {
        e.preventDefault();

        const currentName = document.getElementById('fullName').value.trim();
        const currentTaxId = document.getElementById('taxId').value.trim();

        const taxIdPattern = /^\d{3}-\d{3}-\d{3}$/;
        if (!taxIdPattern.test(currentTaxId)) {
            alert('عذراً، الرقم الضريبي يجب أن يكون بصيغة (000-000-000). أستاذ بيومي بينصحك تراجع الرقم تاني.');
            return;
        }

        const isFraud = fraudDatabase.some(entry =>
            entry.name.includes(currentName) || entry.taxId === currentTaxId
        );

        if (isFraud) {
            alert('تنبيه أستاذ بيومي: لا يمكن إتمام المعاملة إلكترونياً بسبب قيود أمنية. يرجى التوجه لفرع مصلحة الضرائب.');
            return;
        }

        // تم إزالة هذا الشرط لأن زر التفريغ يضمن وجود الملف وتعبئة البيانات
        // if (!fileUpload.files.length) {
        //     alert('يرجى رفع المستندات الداعمة أولاً.');
        //     return;
        // }

        // إظهار شاشة النجاح
        mainContent.style.display = 'none';
        successScreen.style.display = 'block';
    });

    // تشغيل مبدئي
    updateAssistant();
});
