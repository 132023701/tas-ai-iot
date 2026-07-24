function doGet(e) {
  var sheet = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();
  
  // Mengambil data dari parameter URL
  var suhu = e.parameter.suhu;
  var kelembaban = e.parameter.kelembaban;
  var timestamp = new Date(); // Mencatat waktu saat data masuk
  
  if (suhu && kelembaban) {
    // Memasukkan data ke baris paling bawah di spreadsheet
    sheet.appendRow([timestamp, parseFloat(suhu), parseFloat(kelembaban)]);
    return ContentService.createTextOutput("Data berhasil disimpan via GET");
  } else {
    return ContentService.createTextOutput("Data tidak lengkap");
  }
}

function doPost(e) {
  var sheet = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();
  
  try {
    // Mengambil data jika dikirim dalam format JSON
    var data = JSON.parse(e.postData.contents);
    var timestamp = new Date();
    
    sheet.appendRow([timestamp, parseFloat(data.suhu), parseFloat(data.kelembaban)]);
    return ContentService.createTextOutput(JSON.stringify({"status": "success"}))
                         .setMimeType(ContentService.MimeType.JSON);
  } catch(error) {
    return ContentService.createTextOutput(JSON.stringify({"status": "error", "message": error.toString()}))
                         .setMimeType(ContentService.MimeType.JSON);
  }
}