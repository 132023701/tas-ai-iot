function hapusDuplikatJitu() {
  var sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName("Data_Realtime");
  var data = sheet.getDataRange().getValues();
  var dataBersih = [data[0]]; // Menyimpan Baris Header
  var jumlahDihapus = 0;
  
  for (var i = 1; i < data.length; i++) {
    var barisSekarang = data[i];
    var barisSebelumnya = dataBersih[dataBersih.length - 1];
    
    var waktuSekarang = new Date(barisSekarang[0]).getTime();
    var waktuSebelumnya = new Date(barisSebelumnya[0]).getTime();
    
    // Logika Jitu: Jika selisih waktu < 12 detik DAN nilai Suhu & Kelembaban sama persis -> DUPLIKAT!
    var selisihWaktuSec = Math.abs(waktuSekarang - waktuSebelumnya) / 1000;
    var suhuSama = barisSekarang[1] == barisSebelumnya[1];
    var kelembabanSama = barisSekarang[2] == barisSebelumnya[2];
    
    if (selisihWaktuSec < 12 && suhuSama && kelembabanSama) {
      jumlahDihapus++; // Lewati / Abaikan baris duplikat ini
    } else {
      dataBersih.push(barisSekarang);
    }
  }
  
  // Timpa sheet dengan data yang sudah bersih total
  sheet.clearContents();
  sheet.getRange(1, 1, dataBersih.length, dataBersih[0].length).setValues(dataBersih);
  Logger.log("Selesai! Berhasil menghapus " + jumlahDihapus + " baris duplikat.");
}