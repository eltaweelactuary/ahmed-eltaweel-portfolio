/**
 * كود جوجل درايف المطور - نسخة نهائية (Plug & Play)
 * 
 * المرجو استبدال الكود الموجود في Apps Script بهذا الكود بالكامل.
 * تم ضبط معرف الشيت (ID) والإيميل الخاص بك مسبقاً.
 */

function doPost(e) {
  // === الإعدادات المثبتة ===
  var sheetId = '1YiM9Sd80olaGFN2PcIDskfFNdXinO1KUB4493-VPFts'; // معرف الشيت الخاص بك
  var sheetName = 'المشتركين'; // تأكد أن هذا هو اسم ورقة العمل
  // سنحاول الإرسال للإيميلين للتأكد من وصول التنبيه
  var adminEmails = 'ahmed.eltaweel.actuary@gmail.com, eltaweel.actuary@gmail.com'; 
  
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
    
    // خريطة لتنسيق البيانات بناءً على أسماء الأعمدة الفعلية في الشيت
    var mapping = {
        "email": "البريد الإلكتروني",
        "gender": "النوع",
        "name": "الاسم بالكامل",
        "dob": "تاريخ الميلاد",
        "height": "الطول (سم)",
        "weight": "الوزن (كجم)",
        "education": "ما هو مستوى تعليمك؟",
        "job": "الوظيفة",
        "skinColor": "لون البشرة",
        "maritalStatus": "ما هي الحالة الاجتماعية الحالية؟",
        "polygamyInfo": "تفاصيل التعدد",
        "hasChildren": "هل يوجد أطفال؟",
        "childrenWithYou": "هل الأطفال معك؟",
        "governorate": "المدينة",
        "takeSpouseAbroad": "إمكانية سفر الزوجة",
        "isSmoker": "التدخين",
        "prayers": "المحافظة على الصلاة",
        "quran": "ورد القرآن",
        "hasHealthIssues": "مشاكل صحية",
        "healthInfo": "تفاصيل الصحة",
        "partnerWork": "عمل الشريك",
        "partnerHijab": "حجاب الزوجة المطلوب",
        "whatsapp": "رقم التواصل (واتساب)",
        "telegram": "اليوزر تليجرام",
        "facebook": "رابط الفيسبوك",
        "bio": "نبذة مختصرة عنك (اختياري)",
        "mankulat": "قائمة المنقولات",
        "photoLink": "رابط الصورة الشخصية"
    };

    // دمج الأعمار إذا كانت موجودة لتطابق عمود الشيت
    if (data['partnerAgeMin'] && data['partnerAgeMax']) {
        data['ما هي الفئة العمرية لشريك الحياة الذي تبحث عنه؟'] = data['partnerAgeMin'] + ' - ' + data['partnerAgeMax'];
    }

    // رفع الصورة إلى جوجل درايف (إذا وُجدت)
    if (data['photoData'] && data['photoType'] && data['photoName']) {
        try {
            var decodedData = Utilities.base64Decode(data['photoData']);
            var blob = Utilities.newBlob(decodedData, data['photoType'], (data['name'] || "صورة") + " - " + data['photoName']);
            var file = DriveApp.getRootFolder().createFile(blob);
            file.setSharing(DriveApp.Access.ANYONE_WITH_LINK, DriveApp.Permission.VIEW);
            data['photoLink'] = file.getUrl();
        } catch(e) {
            data['photoLink'] = "خطأ في رفع الصورة: " + e.message;
        }
        // مسح بيانات الصورة الخام حتى لا تتسبب في مشكلة في الإيميل أو الشيت
        delete data['photoData'];
        delete data['photoType'];
        delete data['photoName'];
    }

    // 1. معالجة وحفظ البيانات في الشيت
    if (!headers || headers.length === 0 || headers[0] === "") {
        // إذا كان الشيت فارغاً، قم بإنشاء العناوين من البيانات الواردة
        headers = Object.keys(data).filter(function(k) { return k !== 'photoData' && k !== 'photo'; });
        sheet.appendRow(headers.map(function(k) { return mapping[k] || k; }));
    }
    
    var rowData = headers.map(function(header) {
      if (header === 'Timestamp') return new Date();
      var englishKey = Object.keys(mapping).find(key => mapping[key] === header);
      return data[header] || data[englishKey] || '';
    });
    
    // إضافة أي بيانات أرسلت ولا يوجد لها عمود في العمود الأخير كـ JSON (مع استبعاد الصورة لأنها نص ضخم جداً)
    var unmappedData = {};
    Object.keys(data).forEach(function(key) {
        if (!headers.includes(key) && !headers.includes(mapping[key]) && key !== 'photoData' && key !== 'photo') {
            unmappedData[key] = data[key];
        }
    });
    if (Object.keys(unmappedData).length > 0) {
        rowData.push(JSON.stringify(unmappedData));
    }
    
    sheet.appendRow(rowData);
    
    // 2. تجميع كل البيانات لإرسالها في الإيميل
    var name = data['name'] || data['الاسم بالكامل'] || 'مشترك جديد';
    var subject = "🚀 تسجيل جديد: " + name + " (منصة توافق)";
    
    var message = "مرحباً أحمد،\n\nلقد وصلك طلب تسجيل جديد. إليك كافة التفاصيل المدخلة:\n\n";
    message += "=============================\n";
    
    for (var key in data) {
        // تجاهل البيانات الفارغة واستبعاد الصورة لأنها كود طويل جداً
        if (data[key] && data[key].toString().trim() !== "" && key !== 'photoData' && key !== 'photo') {
            var label = mapping[key] || key;
            message += "🔸 " + label + ":\n" + data[key] + "\n\n";
        }
    }
    
    message += "=============================\n\n";
    message += "تم حفظ البيانات في الشيت المربوط بالنظام.";
    
    GmailApp.sendEmail(adminEmails, subject, message);
    
    return ContentService.createTextOutput(JSON.stringify({ "status": "success" }))
      .setMimeType(ContentService.MimeType.JSON);
      
  } catch (err) {
    return ContentService.createTextOutput(JSON.stringify({ "status": "error", "message": err.toString() }))
      .setMimeType(ContentService.MimeType.JSON);
  }
}

/**
 * دالة لتجربة الإيميل وتفعيل التصاريح
 * اختر هذه الدالة من القائمة العلوية في Apps Script واضغط Run
 */
function testEmail() {
  // هذه الخطوة فقط لإجبار جوجل على طلب صلاحيات الدرايف والإيميل
  DriveApp.getRootFolder(); 
  
  var adminEmails = 'ahmed.eltaweel.actuary@gmail.com, eltaweel.actuary@gmail.com';
  GmailApp.sendEmail(adminEmails, "اختبار منصة توافق (نسخة مطورة)", "إذا وصلت هذه الرسالة، فالتصاريح تعمل بنجاح والإيميل صحيح!");
  Logger.log("تم إرسال إيميل تجريبي وتفعيل تصاريح الدرايف بنجاح!");
}
