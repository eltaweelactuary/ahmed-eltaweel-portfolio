/**
 * كود جوجل درايف المطور - نسخة نهائية (Plug & Play)
 * 
 * المرجو استبدال الكود الموجود في Apps Script بهذا الكود بالكامل.
 * تم ضبط معرف الشيت (ID) والإيميل الخاص بك مسبقاً.
 */

function doPost(e) {
  // === الإعدادات المثبتة ===
  var sheetId = '1-Wlq_U6T-y-i2mR6yWf8PqI6bY9v-02E0p6E2o8P_E'; // معرف الشيت الخاص بك
  var sheetName = 'المشتركين'; // تأكد أن هذا هو اسم ورقة العمل
  var adminEmail = 'ahmed.eltaweel.actuary@gmail.com'; 
  
  try {
    var rawData = e.postData.contents;
    var data = JSON.parse(rawData);
    var sheet = SpreadsheetApp.openById(sheetId).getSheetByName(sheetName);
    
    if (!sheet) {
        // إذا لم يجد ورقة بهذا الاسم، سيستخدم أول ورقة عمل في الملف
        sheet = SpreadsheetApp.openById(sheetId).getSheets()[0];
    }

    // استخراج أسماء الأعمدة (العناوين)
    var headers = sheet.getRange(1, 1, 1, sheet.getLastColumn()).getValues()[0];
    
    // خريطة لتنسيق البيانات (تدعم الأسماء بالعربي والإنجليزي)
    var mapping = {
        "email": "البريد الإلكتروني",
        "gender": "النوع",
        "name": "الاسم بالكامل",
        "dob": "تاريخ الميلاد",
        "education": "المؤهل الدراسي",
        "job": "الوظيفة",
        "skinColor": "لون البشرة",
        "maritalStatus": "الحالة الاجتماعية",
        "governorate": "المحافظة",
        "whatsapp": "واتساب",
        "telegram": "تليجرام",
        "facebook": "فيسبوك",
        "bio": "نبذة"
    };

    var rowData = headers.map(function(header) {
      // نحاول البحث عن البيانات بالاسم الإنجليزي للحقل أو الاسم العربي للعمود
      var englishKey = Object.keys(mapping).find(key => mapping[key] === header);
      return data[header] || data[englishKey] || '';
    });
    
    // 1. تسجيل البيانات في الشيت
    sheet.appendRow(rowData);
    
    // 2. إرسال التنبيه عبر البريد
    var name = data['name'] || data['الاسم بالكامل'] || 'مشترك جديد';
    var subject = "🚀 تسجيل جديد: " + name + " (منصة توافق)";
    var message = "مرحباً أحمد،\n\nلقد وصلك طلب تسجيل جديد.\n\n" +
                  "📌 التفاصيل الأساسية:\n" +
                  "------------------\n" +
                  "الاسم: " + name + "\n" +
                  "النوع: " + (data['gender'] || 'غير محدد') + "\n" +
                  "الوظيفة: " + (data['job'] || 'غير محدد') + "\n" +
                  "التواصل: " + (data['whatsapp'] || 'غير مسجل') + "\n" +
                  "------------------\n\n" +
                  "يرجى مراجعة الشيت للاطلاع على باقي البيانات.";
    
    MailApp.sendEmail(adminEmail, subject, message);
    
    return ContentService.createTextOutput(JSON.stringify({ "status": "success" }))
      .setMimeType(ContentService.MimeType.JSON);
      
  } catch (err) {
    return ContentService.createTextOutput(JSON.stringify({ "status": "error", "message": err.toString() }))
      .setMimeType(ContentService.MimeType.JSON);
  }
}
