/**
 * Tawafuq Multi-step Form Backend - V2
 * 
 * IMPORTANT DEPLOYMENT INSTRUCTIONS:
 * 1. Copy this code and replace the old code in your Apps Script editor.
 * 2. Click "Deploy" > "Manage deployments".
 * 3. Click the pencil icon (Edit) next to your active deployment.
 * 4. Under "Version", select "New version".
 * 5. Click "Deploy".
 */

const FOLDER_ID = "YOUR_GOOGLE_DRIVE_FOLDER_ID_HERE"; // Optional: to save photos

function doPost(e) {
  try {
    const data = JSON.parse(e.postData.contents);
    const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheets()[0];
    
    let photoUrl = "";
    
    // 1. Handle Photo Upload to Drive (if exists)
    if (data.photoData && FOLDER_ID !== "YOUR_GOOGLE_DRIVE_FOLDER_ID_HERE") {
      try {
        const folder = DriveApp.getFolderById(FOLDER_ID);
        const decodedData = Utilities.base64Decode(data.photoData);
        const blob = Utilities.newBlob(decodedData, data.photoType, data.photoName || "photo.jpg");
        const file = folder.createFile(blob);
        photoUrl = file.getUrl();
      } catch (uploadError) {
        console.error("Photo upload failed", uploadError);
      }
    }
    
    // 2. Define Strict Headers (This solves the missing headers issue)
    const HEADERS = [
      "Timestamp", // 0
      "الاسم بالكامل", // 1
      "العمر", // 2
      "المدينة", // 3
      "الوظيفة", // 4
      "أنا...", // 5
      "رقم التواصل (واتساب)", // 6
      "نبذة مختصرة عنك (اختياري)", // 7
      "ما هو مستوى تعليمك؟", // 8
      "ما هي الحالة الاجتماعية الحالية؟", // 9
      "على مقياس من 1 إلى 5، ما مدى جدية بحثك عن شريك؟", // 10
      "ما هي الفئة العمرية لشريك الحياة الذي تبحث عنه؟", // 11
      "ما هي الخصائص أو الصفات الرئيسية التي تبحث عنها في شريك حياتك؟ (اختر ما يصل إلى 3)", // 12
      "هل أنت مستعد للانتقال للعيش في مدينة أخرى من أجل الزواج؟", // 13
      // --- New Fields ---
      "البريد الإلكتروني", // 14
      "رابط الصورة الشخصية", // 15
      "تاريخ الميلاد", // 16
      "الطول (سم)", // 17
      "الوزن (كجم)", // 18
      "لون البشرة", // 19
      "تفاصيل التعدد", // 20
      "هل يوجد أطفال؟", // 21
      "هل الأطفال معك؟", // 22
      "إمكانية سفر الزوجة", // 23
      "التدخين", // 24
      "المحافظة على الصلاة", // 25
      "ورد القرآن", // 26
      "مشاكل صحية", // 27
      "تفاصيل الصحة", // 28
      "حالة الشريك الاجتماعية المطلوبة", // 29
      "عمل الشريك", // 30
      "حجاب الزوجة المطلوب", // 31
      "اليوزر تليجرام", // 32
      "رابط الفيسبوك", // 33
      "قائمة المنقولات" // 34
    ];

    // Force headers to row 1 every time (fixes the issue of missing/unchanging headers)
    sheet.getRange(1, 1, 1, HEADERS.length).setValues([HEADERS]);
    
    // Calculate Age
    let age = "";
    if (data.dob && data.dob.includes("-")) {
        const birthYear = parseInt(data.dob.split("-")[0]);
        if (!isNaN(birthYear)) age = new Date().getFullYear() - birthYear;
    }

    // 3. Prepare Row Data to map EXACTLY to the old and new columns
    const row = [
      new Date(), // 0
      data.name || "", // 1
      age, // 2
      data.governorate || "", // 3
      data.job || "", // 4
      (data.gender === "ذكر") ? "شاب أبحث عن زوجة" : "شابة أبحث عن زوج", // 5
      data.whatsapp || "", // 6
      data.bio || "", // 7
      data.education || "", // 8
      data.maritalStatus || "", // 9
      "5", // 10 (Default seriousness)
      (data.partnerAgeMin && data.partnerAgeMax) ? (data.partnerAgeMin + " - " + data.partnerAgeMax) : "", // 11
      "", // 12 (Old characteristics field)
      data.isExpat || "", // 13
      data.email || "", // 14
      photoUrl, // 15
      data.dob || "", // 16
      data.height || "", // 17
      data.weight || "", // 18
      data.skinColor || "", // 19
      data.polygamyInfo || "", // 20
      data.hasChildren || "", // 21
      data.childrenWithYou || "", // 22
      data.takeSpouseAbroad || "", // 23
      data.isSmoker || "", // 24
      data.prayers || "", // 25
      data.quran || "", // 26
      data.hasHealthIssues || "", // 27
      data.healthInfo || "", // 28
      data.partnerStatus || "", // 29
      data.partnerWork || "", // 30
      data.partnerHijab || "", // 31
      data.telegram || "", // 32
      data.facebook || "", // 33
      data.mankulat || "" // 34
    ];
    
    sheet.appendRow(row);
    
    return ContentService.createTextOutput("Success").setMimeType(ContentService.MimeType.TEXT);
    
  } catch (err) {
    return ContentService.createTextOutput("Error: " + err.toString()).setMimeType(ContentService.MimeType.TEXT);
  }
}
