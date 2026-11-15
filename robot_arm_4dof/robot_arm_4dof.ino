#include <Wire.h>
#include <Adafruit_PWMServoDriver.h>
#include <SoftwareSerial.h>

SoftwareSerial BT(2, 3);

Adafruit_PWMServoDriver boDieuKhienPwm = Adafruit_PWMServoDriver(0x40);

#define XUNG_TOI_THIEU      125
#define XUNG_TOI_DA         575
#define BUOC_TAY_MAY        2
#define BUOC_KEP            5

#define KENH_KEP            3
#define GOC_MO_HET_CO       95
#define GOC_DONG_TOI_DA     160

int gocDe    = 0;
int gocVai   = 90;
int gocKhuyu = 90;
int gocKep   = GOC_MO_HET_CO;

unsigned long thoiGianGuiCuoi = 0;

void datGocServo(uint8_t kenh, int goc) {
  int doRongXung = map(goc, 0, 180, XUNG_TOI_THIEU, XUNG_TOI_DA);
  boDieuKhienPwm.setPWM(kenh, 0, doRongXung);
}

void guiTrangThaiServo() {
  Serial.print("{\"t\":");
  Serial.print(millis());
  Serial.print(",\"servo\":[");
  Serial.print(gocDe);    Serial.print(",");
  Serial.print(gocVai);   Serial.print(",");
  Serial.print(gocKhuyu); Serial.print(",");
  Serial.print(gocKep);
  Serial.print("],\"relax\":0,\"armrelax\":0}");
  Serial.println();
}

void setup() {
  Serial.begin(9600);
  BT.begin(9600);

  boDieuKhienPwm.begin();
  boDieuKhienPwm.setPWMFreq(50);

  datGocServo(0, gocDe);
  datGocServo(1, gocVai);
  datGocServo(2, gocKhuyu);
  datGocServo(KENH_KEP, gocKep);

  delay(500);
  Serial.println("Robot Arm Ready! WASD + IK + JL + H");
  guiTrangThaiServo();
  thoiGianGuiCuoi = millis();
}

void loop() {
  char kyTuLenh = 0;
  if (BT.available()) {
    kyTuLenh = BT.read();
  } else if (Serial.available()) {
    kyTuLenh = Serial.read();
  }

  if (kyTuLenh != 0) {
    bool lenhHopLe = true;

    switch (kyTuLenh) {
      case 'a': case 'A':
        gocDe = constrain(gocDe + BUOC_TAY_MAY, 0, 180);
        break;
      case 'd': case 'D':
        gocDe = constrain(gocDe - BUOC_TAY_MAY, 0, 180);
        break;

      case 'w': case 'W':
        gocVai = constrain(gocVai + BUOC_TAY_MAY, 25, 155);
        break;
      case 's': case 'S':
        gocVai = constrain(gocVai - BUOC_TAY_MAY, 25, 155);
        break;

      case 'i': case 'I':
        gocKhuyu = constrain(gocKhuyu + BUOC_TAY_MAY, 25, 155);
        break;
      case 'k': case 'K':
        gocKhuyu = constrain(gocKhuyu - BUOC_TAY_MAY, 25, 155);
        break;

      case 'j': case 'J':
        gocKep = constrain(gocKep - BUOC_KEP, GOC_MO_HET_CO, GOC_DONG_TOI_DA);
        break;
      case 'l': case 'L':
        gocKep = constrain(gocKep + BUOC_KEP, GOC_MO_HET_CO, GOC_DONG_TOI_DA);
        break;

      case 'h': case 'H':
        gocDe    = 0;
        gocVai   = 90;
        gocKhuyu = 90;
        gocKep   = GOC_MO_HET_CO;
        break;

      default:
        lenhHopLe = false;
        break;
    }

    if (lenhHopLe) {
      Serial.print("Phím bấm: ");
      Serial.println(kyTuLenh);

      datGocServo(0, gocDe);
      datGocServo(1, gocVai);
      datGocServo(2, gocKhuyu);
      datGocServo(KENH_KEP, gocKep);

      guiTrangThaiServo();
      thoiGianGuiCuoi = millis();
    }
  }

  if (millis() - thoiGianGuiCuoi >= 200) {
    thoiGianGuiCuoi = millis();
    guiTrangThaiServo();
  }
}
