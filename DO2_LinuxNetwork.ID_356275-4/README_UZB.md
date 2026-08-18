# Linux da tarmoqlar 

Virtual mashinalarda Linuxda tarmoqlarni sozlash.

💡 Ushbu loyiha bo’yicha fikr-mulohazalaringizni biz bilan baham ko’rish uchun [**shu yerni bosing**](https://new.oprosso.net/p/4cb31ec3f47a4596bc758ea1861fb624). Bu anonim va jamoamizga mashg'ulotlarni yaxshilashga yordam beradi. Loyihani tugatgandan so'ng darhol so'rovnomani to'ldirishni tavsiya qilamiz.

## Contents 

1. [Chapter I](#chapter-i)
2. [Chapter II](#chapter-ii) \
    2.1. [TCP IP bayonnomalar to’plami](#tcp-ip-bayonnomalar-toplami) \
    2.2. [Manzillash](#manzillash) \
    2.3. [Marshrutlash](#marshrutlash)
3. [Chapter III](#chapter-iii) \
    3.1. [ipcalc vositasi](#part-1-ipcalc-vositasi) \
    3.2. [Ikki mashina o'rtasida statik marshrutizatsiya](#part-2-ikki-mashina-ortasida-statik-marshrutizatsiya) \
    3.3. [iperf3 utilitasi](#part-3-iperf3-utilitasi) \
    3.4. [Tarmoqli ekran](#part-4-tarmoqli-ekran) \
    3.5. [Tarmoqning static marshrutizatsiyasi](#part-5-tarmoqning-static-marshrutizatsiyasi) \
    3.6. [DHCP yordamida IP ni dinamik sozlash](#part-6-dhcp-yordamida-ip-ni-dinamik-sozlash) \
    3.7. [NAT](#part-7-nat) \
    3.8. [Qo'shimcha ravishda. SSH Tunnels bilan tanishish](#part-8-qoshimcha-ravishda-ssh-tunnels-bilan-tanishish)
4. [Chapter IV](#chapter-iv)

## Chapter I

![linux_network](misc/images/linux_network.png)

Yer sayyorasi, Seb’s jaz-klubi, hozirgi kunlar.

\> *Barda yangi jaz guruhi kuylamoqda. Ularning qo’shig’i sen ko’nikkaningdan sal jo’shqinroq, lekin ularning iste'dodini inkor eta olmaysiz.*

`-` Sebastyan, sen bir haftadan beri ofis stolida o'tiribsan. Seningcha, sen Linuxda ishlashni organdingmi? Biroq, hafta o'rtasida yana qo'ng'iroq qilganingni hisobga olsak, javobni shunday ham bilaman deb o'ylayman ...

`-` Asta-sekin tushunib boryapman, lekin o’zim xohlaganimdek tez emas.

`-` Ertaga ishga chiqishga tayyormisan?

`-` Men tushunmayapman, tushunmayapman o’rtoq. Menga: tarmoqlarni sozlash bilan shug’ullan deyishyapti. Lekin men uchun bu shunchaki so’zlar. Men oldingi o’zim bilan, tizim administratori ishiga rozi bo’lgan yosh axmoq yigit bilan uchrashib, uni fikridan qaytarishni, hammasini tushuntirishni xohlayman, ammo buning iloji yo’q. Nima qilay do’stim? 

`-` Umidsizlikka tushma. Tarmoqlarni sozlash unchalik qo’rqinchli emas. Agar bitta savolga javob bersang, mamnuniyat bilan javob beraman: nega otang seni aynan tizim administratori qilib ishga joyladi? Axir biz uning barida o'tiramiz, nega bu yerga joylamadi? Bu ancha osonroq.

`-` O’zim ham bilmayman, qariyani miyasida nimaligini kim bilsin. Mustaqil bo’lish va dunyoqarashini kengaytirish haqida nimalardir deydi...

`-` Yaxshi, unda dunyoqarashingni kengaytirishda davom etamiz. Noutbukingni qo’linga ol, virtual mashinangni ko’tar, nima qanday ekanligini ko’rsataman.

\> *Yangi qo’shiqchilar o’rniga barning doimiy qo’shiqchilari chiqishadi, musiqa sekinlashadi, ofitsiant buyurtmangizni hali keltirgani yo’q*

\>  *Sebastyan asta - sekin virtual mashinani ko'targuncha, sen Linuxda tarmoqqa oid asosiy ma'lumotlarni baham ko'rishga qaror qilding.*

## Chapter II

### TCP IP bayonnomalar to’plami

Aslida, tarmoq nima? Tarmoq bu - ba'zi bir aloqa kanallari yoki murakkabroq holatlarda ba'zi tarmoq uskunalari yordamida kamida ikkita kompyuterning ulanishi. Ular o'rtasida ma'lumotlar almashinuvi ma'lum qoidalarga muvofiq amalga oshiriladi va bu qoidalar TCP/IP bayonnomalar to’plami tomonidan "ta’kidlanadi".

Transmission Control Protocol/Internet Protocol (**TCP/IP** bayonnomalar to’plami) - oddiy so'z bilan aytganda, bu turli darajadagi o'zaro ta'sir qiluvchi bayonnomalar to'plamidir (har bir daraja yonidagisi bilan o'zaro ta'sir qiladi, ya'ni ular tutashadi, shuning uchun ham stek), unga ko'ra ma'lumotlar tarmoqda almashildi.

Xulosa qilib aytadigan bo'lsak, TCP/IP protokollari to'plami bu erda o'rtacha savol tug'ilishi mumkin: nima uchun protokollar ko'p? Bitta protokol yordamida hamma narsani almashtirish haqiqatan ham mumkin emasmi?

Gap shundaki, har bir protokol unga qat'iy belgilangan qoidalarni tavsiflaydi. Bundan tashqari, protokollar funksionallik darajalariga bo'linadi, bu tarmoq uskunalari va dasturiy ta'minotning ishlashini ancha sodda, shaffofroq qilish va "o'z" vazifalarini bajarish imkonini beradi. Ushbu protokollar to'plamini qatlamlarga bo'lish uchun OSI tarmog'ining o'zaro ta'siri modeli (Open Systems Interconnection Basic Reference Model, 1978, shuningdek, ochiq tizimlarning o'zaro ta'siri uchun asosiy mos yozuvlar modeli sifatida ham tanilgan) ishlab chiqilgan. OSI modeli yetti xil qatlamdan iborat. Daraja aloqa tizimlarining ishlashida alohida bo'lim uchun javobgardir, qo'shni darajalarga bog'liq emas - u faqat ma'lum xizmatlarni taqdim etadi. Har bir qatlam o'z vazifasini protokol deb ataladigan qoidalar to'plamiga muvofiq bajaradi.

### Manzillash

**TCP/IP** protokoli stekiga qurilgan tarmoqda har bir xostga (tarmoqqa ulangan kompyuter yoki qurilma) IP manzili beriladi.

IP-manzil 32 bitli ikkilik raqamdir.

IP-manzilni (**IPv4**) yozishning qulay shakli nuqtalar bilan ajratilgan to'rtta o'nlik raqam (0 dan 255 gacha), masalan, *192.168.0.1*.

Umuman olganda, IP-manzil ikki qismga bo'linadi: tarmoq (pastki tarmoq) manzili va xost manzili:

![subnetwork_mask](misc/images/subnetwork_mask.png)

Rasmdan ko'rinib turibdiki, tarmoq va quyi tarmoq kabi tushunchalar mavjud.

Menimcha, so‘zlarning ma’nosidan IP-manzillar tarmoqlarga, tarmoqlar esa o‘z navbatida pastki tarmoq niqobi yordamida quyi tarmoqlarga bo‘linishi aniq ko‘rinib turibdi (to‘g‘riroq qilib aytsak: xost manzili quyi tarmoqlarga bo‘linishi mumkin).

Xost manziliga qo'shimcha ravishda, TCP/IP tarmog'ida port deb ataladigan tushuncha mavjud. Port - tizim resursining raqamli xarakteristikasi.

Port tarmoq xostida ishlaydigan ilovaga boshqa tarmoq xostlarida ishlaydigan ilovalar (shu jumladan bir xil xostdagi boshqa ilovalar) bilan aloqa qilish uchun ajratilgan. Dasturiy ta'minot nuqtai nazaridan port - bu ba’zi bir xizmat tomonidan boshqariladigan xotira maydoni.

IP protokoli protokol ierarxiyasida **TCP** va **UDP** dan pastda joylashgan va tarmoqdagi ma'lumotlarni uzatish va yo'naltirish uchun javobgardir.

Buning uchun IP protokoli har bir ma'lumot blokini (**TCP** yoki **UDP** paketi) manba, maqsad va marshrut haqidagi sarlavhani saqlaydigan boshqa paketga - IP-paket yoki IP-datagrammaga qamrab oladi.

Haqiqiy dunyo bilan o'xshashlik qilsak, **TCP/IP** tarmog'i bu-shahar. Ko'cha va xiyobon nomlari tarmoqlar va quyi tarmoqlardir. Bino raqamlari xost manzillari.

Binolarda ofis/xonadon raqamlari portlardir. Aniqroq aytganda, portlar pochta qutilari bo'lib, ularda qabul qiluvchilar (xizmatlar) korrespondentlar kelishini kutadilar.

Shunga ko’ra, ofis port raqamlari 1, 2 va boshqalar odatda direktorlar va menejerlarga imtiyozli shaxslar sifatida beriladi va oddiy xodimlar katta raqamlar bilan ofis raqamlarini oladi. Xat-xabarlarni jo'natish va yetkazib berishda ma'lumotlar konvertlarga (IP-paketlarga) o'raladi, ularda jo'natuvchining manzili (IP va port) va qabul qiluvchining manzili (IP va port) ko'rsatilgan.

Shuni ta'kidlash kerakki, IP protokoli portlar to’g’risida tushunchaga ega emas, **TCP** va **UDP** portlarni xuddi shunday talqin qilish uchun javobgardir;

### Marshrutlash

![network_route](misc/images/network_route.png)

Savol tug'ilishi mumkin, bir kompyuter boshqasiga qanday ulanadi?

U paketlarni qayerga yuborishni qayerdan biladi?

Ushbu muammoni hal qilish uchun tarmoqlar bir-biriga shlyuzlar (marshrutizatorlar) orqali ulanadi.

Shlyuz bir xil xost, lekin ikki yoki undan ortiq tarmoqqa ulanishga ega bo'lib, u tarmoqlar o'rtasida ma'lumot uzatishi va paketlarni boshqa tarmoqqa yo'naltirishi mumkin.

Rasmda shlyuz rolini pineapple va papaya o'ynaydi, ularning har biri turli tarmoqlarga ulangan 2 ta interfeysga ega.

Paketni uzatish marshrutini aniqlash uchun IP manzilning tarmoq qismidan (pastki tarmoq niqobi) foydalanadi.

Marshrutni aniqlash uchun tarmoqdagi har bir mashinada ushbu tarmoqlar uchun tarmoqlar va shlyuzlar ro'yxatini saqlaydigan marshrutlash jadvali mavjud.

IP o’tayotgan paketdagi maqsad manzilining tarmoq qismini "izlaydi" va agar marshrutlash jadvalida ushbu tarmoq uchun yozuv mavjud bo'lsa, u holda paket tegishli shlyuzga yuboriladi.

Linuxda operatsion tizim yadrosi marshrutlash jadvalini */proc/net/route* faylida saqlaydi.

Joriy marshrutlash jadvalini `netstat -rn` (r – routing table, n - IPni nomlarga aylantirmang), `route` yoki `ip r` buyrug'i bilan ko'rishingiz mumkin.

eggplant xostiga misol marshrutizatsiya jadvali:
```
[root@eggplant ~]# netstat -rn
Kernel IP routing table
Destination     Gateway         Genmask         Flags   MSS Window  irtt Iface
128.17.75.0      128.17.75.20   255.255.255.0   UN        1500 0          0 eth0
default          128.17.75.98   0.0.0.0         UGN       1500 0          0 eth0
127.0.0.1        127.0.0.1      255.0.0.0       UH        3584 0          0 lo
128.17.75.20     127.0.0.1      255.255.255.0   UH        3584 0          0 lo
```

Ustunlar qiymatlari: 
- Destination — manzil tarmoqlarining manzillari (xostlar). Shu bilan birga, tarmoqni ko'rsatishda manzil - odatda nol bilan tugaydi; 
- Gateway - birinchi ustunda ko'rsatilgan xost/tarmoq uchun shlyuz manzili. Uchinchi ustun - bu marshrut - ishlaydigan pastki tarmoq niqobi; 
- Flags - manzil manzili haqida ma'lumot (U - marshrut ishlamoqda, N - tarmoq uchun marshrut, H - xost uchun marshrut va boshqalar); 
- MSS - bir vaqtning o'zida yuborilishi mumkin bo'lgan baytlar soni; 
- Window — tasdiqnomani olishdan oldin yuborilishi mumkin bo'lgan kadrlar soni; 
- irtt — marshrutdan foydalanish statistikasi; 
- Iface - marshrut uchun ishlatiladigan tarmoq interfeysini ko'rsatadi (eth0, eth1 va boshqalar).

\> *O’tgan safardagi kabi, siz materials papkasida yanada foydali ma'lumotlarni topasiz.*

## Chapter III

Ishingiz natijasida siz bajarilgan vazifalar haqida hisobot topshirishingiz kerak. Vazifaning har bir qismida hisobot tugagandan so'ng unga nima kiritilishi kerakligi ko'rsatilgan. Bu savollarga javoblar, skrinshotlar va boshqalar bo'lishi mumkin.

- .md kengaytmali hisobot src papkasida joylashgan omborga yuklanishi kerak.
- Hisobot topshiriqning barcha qismlarini 2-darajali sarlavha sifatida ajratib ko'rsatishi kerak.
- Topshiriqning bir qismida hisobotga kiradigan hamma narsa ro'yxat sifatida formatlanishi kerak.
- Hisobotdagi har bir skrinshot qisqacha belgilanishi kerak (skrinshotda ko'rsatilganidek).
- Barcha skrinshotlar ekranning faqat kerakli qismi ko'rinadigan tarzda kesilgan.
- Bitta skrinshotda bir vaqtning o'zida bir nechta vazifa nuqtalarini ko'rsatishga ruxsat beriladi, ammo ularning barchasi skrinshotning sarlavhasida tasvirlangan bo'lishi kerak.
- Vazifa davomida yaratilgan barcha virtual mashinalarda o'rnating **Ubuntu 20.04 Server LTS**.

Utilitalar ro’yxati: `ipcalc`, `ip`, `netplan`, `netstat`, `iperf3`, `iptables`, `ping`, `nmap`, `sysctl`, `tcpdump`, `traceroute`, `systemctl`, `telnet`, `dhclient`, `isc-dhcp-server`, `apache2`.

## Part 1. **ipcalc** vositasi

`-` Shunday qilib, keling, IP-manzillar bilan tanishish orqali ajoyib tarmoqlar olamiga kirishni boshlaylik. Buning uchun biz **ipcalc** vositasidan foydalanamiz. 

**== Topshiriq ==**

##### Virtual mashinani ko'taring (keyingi o'rinlarda ws1 deb yuritiladi)

#### 1.1. Tarmoqlar va niqoblar

##### Aniqla va hisobotga yozib qo’y:

##### 1) Tarmoq manzili *192.167.38.54/13*
##### 2) 255.255.255.0 niqobini prefiks va ikkilik yozuvga, */15* ni oddiy va ikkilik belgilarga aylantirish, *11111111.11111111.11111111.11110000* oddiy va prefiksda
##### 3) */8, 11111111.11111111.00000000.00000000, 255.255.254.0* va */4* niqoblarida *12.167.38.4* tarmog'idagi minimal va maksimal xost*

#### 1.2. localhost
##### Quyidagi IP manzillari bilan localhost-da ishlayotgan dastur bilan bog'lanish mumkinligini aniqlang va hisobotga yozing: *194.34.23.100, 127.0.0.2, 127.1.0.1, 128.0.0.1*

#### 1.3. Tarmoqlar diapazonlari va segmentlari  
##### Aniqlang va hisobotga yozing:  
##### 1) Quyidagi IP-lardan qaysilarini jamoat (ommaviy) sifatida, qaysilarini esa faqat shaxsiy sifatida ishlatish mumkin: *10.0.0.45*, *134.43.0.2*, *192.168.4.2*, *172.20.250.4*, *172.0.2.1*, *192.172.0.1*, *172.68.0.2*, *172.16.255.255*, *10.10.10.10*, *192.169.168.1*  
##### 2) *10.10.0.0/18* tarmog‘ida quyidagi IP-manzillardan qaysilari shlyuz manzili bo‘lishi mumkin: *10.0.0.1*, *10.10.0.2*, *10.10.10.10*, *10.10.100.1*, *10.10.1.255*  

## Part 2. Ikki mashina o'rtasida statik marshrutizatsiya

`-` Keling, statik marshrutlash yordamida ikkita mashinani qanday ulashni aniqlaylik.

**== Topshiriq ==**

##### Ikkita virtual mashinani ishga tushiring (keyingi o‘rinlarda — **ws1** va **ws2**).

##### Mavjud tarmoq interfeyslarini ko'rish uchun `ip a` buyrug'idan foydalaning.
- Hisobotda foydalanilgan buyruqning chaqiruvi va chiqishi bilan skrinshotni joylashtiring. 
##### Ikkala mashinada ham ichki tarmoqqa mos keladigan tarmoq interfeysini tavsiflang va quyidagi manzillar va niqoblarni belgilang: ws1 - *192.168.100.10*, niqob /16, ws2 - *172.24.116.8*, niqob /12.
- Hisobotda har bir mashina uchun o'zgartirilgan *etc/netplan/00-installer-config.yaml* faylining mazmunini o'z ichiga olgan skrinshotlarni joylashtiring.
##### Tarmoq xizmatini qayta ishga tushirish uchun netplan application buyrug'ini ishga tushiring.
- Hisobotda foydalanilgan buyruqning chaqiruvi va chiqishi bilan skrinshotni joylashtiring.

#### 2.1. Statik marshrutni qo'lda qo'shish
##### `ip r add` kabi buyruq yordamida bir mashinadan ikkinchisiga va orqaga statik marshrut qo'shing.
##### Mashinalar orasidagi ulanishni ping qiling.
- Hisobotda foydalanilgan buyruqlarning chaqiruvi va chiqishi bilan skrinshotni joylashtiring.

#### 2.2. Saqlash bilan statik marshrut qo'shish
##### Mashinalarni qayta ishga tushiring.
##### */etc/netplan/00-installer-config.yaml fayli yordamida bir mashinadan ikkinchisiga statik marshrut qo'shing.*
- Hisobotda o'zgartirilgan */etc/netplan/00-installer-config.yaml* faylining mazmunini o'z ichiga olgan skrinshotni joylashtiring.
##### Mashinalar orasidagi ulanishni ping qiling.
- Hisobotda foydalanilgan buyruqning chaqiruvi va chiqishi bilan skrinshotni joylashtiring.

## Part 3. **iperf3** utilitasi 

`-` Endi biz ikkita mashinani ulab olganimizdan so’ng, menga javob bering: mashinalar o'rtasida ma'lumot uzatishda eng muhimi nima? 

`-` Ulanish tezligi? 

`-` To’ppa-to'g'ri. Biz buni **iperf3** utilitasi yordamida tekshiramiz.

**== Topshiriq ==**

*Ushbu topshiriqda 2 Qismdagi ws1 va ws2 virtual mashinalaridan foydalaniladi*

#### 3.1. Ulanish tezligi
##### O'zgartiring va hisobotga yozing: 8 Mbit / s dan MB / s ga, 100 MB / s dan Kbit ga, 1 Gbit / s dan Mbps ga.

#### 3.2. iperf3 utilitasi 
##### Ws1 va ws2 o'rtasidagi ulanish tezligini o'lchang.
- Hisobotda foydalanilgan buyruqlarning chaqiruvi va chiqishi bilan skrinshotlarni joylashtiring.

## Part 4. Tarmoqli ekran

`-` Mashinalarni ulagandan so'ng, biz quyidagi vazifaga duch kelamiz: ulanish orqali o'tadigan ma’lumotlarni boshqarish. Bu maqsadda tarmoq ekranlari qo'llaniladi.

**== Topshiriq ==**

*Ishbu topshiriqda 2-qismdagi ws1 va ws2 virtual mashinalaridan foydalanadi*

#### 4.1. iptables utilitasi*
##### ws1 va ws2 da fayrvolni imitatsiya qiluvchi */etc/firewall.sh* faylini yarating:
```shell
#!/bin/sh

# “filter” (по умолчанию) jadvalida barcha qoidalarni o’chirish.
iptables -F
iptables -X
```
##### Faylga ketma-ket quyidagi qoidalarni qo’shish kerak:
##### 1) ws1 da boshida taqiqlovchi qoida va oxirida ruxsat berish qoidasi yozilgan strategiyani qo'llang (bu 4 va 5 ndlarga tegishli).
##### 2) ws2 da ruxsat beruvchi qoida boshida va taqiqlovchi qoida oxirida yoziladigan strategiyani qo'llang (bu 4 va bandlarga tegishli).
##### 3) 22 (ssh) va 80 (http) portlari uchun mashinalarda ochiq kirish.
##### 4) *Echo reply* taqiqlash (mashina "ping" qilmasligi kerak, ya’ni OUTPUT bloklanishi kerak).
##### 5) *Echo reply* ruxsat bering (mashina ping qilishi kerak).
- Hisobotda har bir mashina uchun */etc/firewall* faylining mazmuni bilan skrinshotlarni joylashtiring.
##### Fayllarni ikkala mashinada `chmod +x /etc/firewall.sh` va `/etc/firewall.sh` buyruqlari bilan ishga tushiring.
- Hisobotda ikkala faylning ishga tushirilishining skrinshotlarini joylashtiring.
- Hisobotingizda birinchi va ikkinchi fayllarda qo'llanilgan strategiyalar o'rtasidagi farqni tasvirlab bering.

#### 4.2. nmap utilitasi
##### **ping** qilmaydigan mashinani topish uchun ping buyrug'idan foydalaning, so'ngra **nmap** yordam dasturidan mashina xosti ishlayotganligini ko'rsating.
*Tekshiring: nmap chiqishi shunday deyishi kerak: `Host is up`*.
- Hisobotda foydalanilgan **ping** va **nmap** buyruqlarining chaqiruvi va chiqishi bilan skrinshotlarni qo'shing.

##### Virtual mashina tasvirlari qoldiqlarini saqlang
**P.S. Hech qanday holatda Git-ga damplarni saqlamang!**

## Part 5. Tarmoqning static marshrutizatsiyasi

`-` Hozirgacha biz faqat ikkita mashinani uladik, ammo endi butun tarmoqni statik marshrutlash vaqti keldi.

**== Topshiriq ==**

Tarmoq: \
![part5_network](misc/images/part5_network.png)

##### Beshta virtual mashinani ko’taring (3 ta ishchi stansiya (ws11, ws21, ws22) va 2 ta router (r1, r2)).

#### 5.1. Mashina adreslarini sozlash

##### Rasmdagi tarmoqqa muvofiq *etc/netplan/00-installer-config.yaml* da mashina konfiguratsiyasini sozlang.
- Hisobotda har bir mashina uchun *etc/netplan/00-installer-config.yaml* faylining mazmuni bilan skrinshotlarni joylashtiring.
##### Tarmoq xizmatini qayta ishga tushiring. Agar xato bo'lmasa, mashina manzili to'g'ri o'rnatilganligini tekshirish uchun `ip -4 a` buyrug'idan foydalaning. Shuningdek, ws22 ni ws21 dan ping qiling. Xuddi shunday, ws11 dan ping r1.
- Hisobotda foydalanilgan buyruqlarning chaqiruvi va chiqishi bilan skrinshotlarni joylashtiring.

#### 5.2. IP -manzillarning yo’naltirilishini yoqish

##### IP yo'qishni ishlatish uchun marshrutizatorlarda buyruqni bajaring:
`sysctl -w net.ipv4.ip_forward=1`
*Bunday yondashuvda qayta yo’naltirish tizimni qayta yuklagandan so’ng ishlamaydi.*
- Hisobotda foydalanilgan buyruqning chaqiruvi va chiqishi bilan ekran tasvirini joylang.
##### */etc/sysctl.conf* faylini oching va unga quyidagi qatorni qo'shing:
`net.ipv4.ip_forward = 1`
*Ushbu yondashuvdan foydalanilganda, IP-qayta yo’naltirish doimiy ravishda yoqilgan.*
- Hisobotda o'zgartirilgan */etc/ysctl.conf.* faylining mazmunini o'z ichiga olgan skrinshotni.

#### 5.3.  marshrutni sozlash

Shlyuzni qo'shgandan so'ng `ip r` buyrug'ining chiqishing namunasi:
```
default via 10.10.0.1 dev eth0 
10.10.0.0/18 dev eth0 proto kernel scope link src 10.10.0.2
```
##### Ish stantsiyalari uchun  marshrutni (shlyuz) sozlang. Buni amalga oshirish uchun konfiguratsiya faylida yo'riqnoma IP-dan oldin default tni qo'shing.
- Hisobotda *etc/netplan/00-installer-config.yaml* faylining mazmunini o'z ichiga olgan skrinshotni joylashtiring;
##### `ip r` ni chaqiring va marshrutlash jadvalida marshrut qo'shilganligini ko'rsating.
- Hisobotda foydalanilgan buyruqning chaqiruvi va chiqishi bilan skrinshotni joylashtiring.
##### ws11 dan ping router r2 va ping qabul qilinayotganini r2 ko'rsating. Buning uchun buyruqdan foydalaning:
`tcpdump -tn -i eth0`
- Hisobotda foydalanilgan buyruqlarning chaqiruvi va chiqishi bilan skrinshotni joylashtiring.

#### 5.4. Statik marshrutlarni qo’shish

##### Konfiguratsiya faylida r1 va r2 marshrutizatorlariga statik marshrutlarni qo'shing. 10.20.0.0/26 tarmog'iga r1 marshrutiga misol:
```shell
# eth1 tarmoq interfeysi tavsifining oxiriga qo'shing:
`-` to: 10.20.0.0 
via: 10.100.0.12
```
- Hisobotda har bir router uchun o'zgartirilgan *etc/netplan/00-installer-config.yaml* faylining mazmunini o'z ichiga olgan skrinshotlarni joylashtiring.
##### `ip r` ni chaqiring va ikkala routerda marshrutlar bilan jadvallarni ko'rsating. r1 dagi jadval misoli:
```
10.100.0.0/16 dev eth1 proto kernel scope link src 10.100.0.11
10.20.0.0/26 via 10.100.0.12 dev eth1
10.10.0.0/18 dev eth0 proto kernel scope link src 10.10.0.1
```
- Hisobotda foydalanilgan buyruqning chaqiruvi va chiqishi bilan skrinshotni joylashtiring.
##### ws11 da quyidagi buyruqlarini ishga tushiring:
`ip r list 10.10.0.0/[tarmoq niqobi] va ip r list 0.0.0.0/0`
- Hisobotda foydalanilgan buyruqlarning chaqiruvi va chiqishi bilan skrinshotni joylashtiring; 
- Hisobotda nima uchun 10.10.0.0/\[tarmoq niqobi\] manzili uchun 0.0.0.0/0 dan boshqa marshrut tanlanganligini tushuntiring, garchi u  marshrut ostida bo'lsa-da.

#### 5.5. Marshrutizatorlar ro’yxatini qurish

Shlyuz qo'shgandan so'ng **traceroute** utilitasining chiqishi misoli:
```
1 10.10.0.1 0 ms 1 ms 0 ms 
2 10.100.0.12 1 ms 0 ms 1 ms 
3 10.20.0.10 12 ms 1 ms 3 ms
```
##### r1-da damp buyrug'ini ishga tushiring:
`tcpdump -tnv -i eth0`
##### Traceroute utilitasidan foydalanib, ws11 dan ws21 gacha bo'lgan yo'lda marshrutizatorlar ro'yxatini tuzing.
- Hisobotda foydalanilgan buyruqlar (tcpdump va traceroute) chaqiruvi va chiqishi bilan skrinshotlarni joylashtiring; 
- Hisobotda, r1 bo'yicha chiqindixonadan olingan natijaga asoslanib, **traceroute** yordamida yo'l qurilishi qanday ishlashi printsipini tushuntiring.

#### 5.6. Marshrutlash uchun ICMP protokolidan foydalanish
##### Buyruq yordamida eth0 orqali o'tayotgan tarmoq trafigini ushlab turish uchun r1 da ishga tushiring:**
`tcpdump -n -i eth0 icmp`
##### Mavjud bo'lmagan IP bilan (masalan, 10.30.0.111) ws11-dan quyidagi buyruq yordamida ping yuboring :
`ping -c 1 10.30.0.111`
- Hisobotda foydalanilgan buyruqlarning chaqiruvi va chiqishi bilan skrinshotni joylashtiring.

##### Virtual mashinalarning rasmlarini saqlang.
**P.S. Hech qanday holatda Git-ga axlatlarni saqlamang!**

## Part 6. DHCP yordamida IP ni dinamik sozlash

`-` Bizning keyingi qadamimiz siz allaqachon bilgan **DHCP** xizmati bilan ko'proq tanishish bo'ladi.

**== Topshiriq ==**

*Ushbu topshiriqda 5-qismdagi virtual mashinalardan foydalanadi.*

##### r2 uchun */etc/dhcp/dhcpd.conf* faylida **DHCP** xizmati konfiguratsiyasini sozlang:** 
##### 1) router manzilini, DNS serverini va ichki tarmoq manzilini belgilang. r2 uchun fayl namunasi:
```shell
subnet 10.100.0.0 netmask 255.255.0.0 {}

subnet 10.20.0.0 netmask 255.255.255.192
{
    range 10.20.0.2 10.20.0.50;
    option routers 10.20.0.1;
    option domain-name-servers 10.20.0.1;
}
```
##### 2) *resolv.conf* faylida `nameserver 8.8.8.8` ni yozing.
- Hisobotda o'zgartirilgan fayllarning mazmuni bilan skrinshotlarni joylashtiring.
##### `systemctl restart isc-dhcp-serve`r buyrug'i yordamida DHCP xizmatini qayta ishga tushiring. `reboot` orqali ws21 mashinasini qayta ishga tushiring va `ip a` orqali u manzilni olganligini ko'rsating. Shuningdek, ws22 ni ws21 dan ping qiling.
- Hisobotda foydalanilgan buyruqlarning chaqiruvi va chiqishi bilan skrinshotlarni joylashtiring.

##### Buning uchun ws11 uchun MAC manzilini belgilang, *etc/netplan/00-installer-config.yaml* ga quyidagi qatorlarni qo'shing: `macaddress: 10:10:10:10:10:BA`, `dhcp4: true`.
- Hisobotda o'zgartirilgan faylning mazmunini o'z ichiga olgan skrinshotni joylashtiring *etc/netplan/00-installer-config.yaml.*
##### r1 uchun sozlash r2 ga o'xshaydi, lekin MAC manziliga (ws11) qat'iy bog'langan manzillarni bering.
##### Shunga o'xshash testlarni o'tkazing.
- Hisobotda ushbu elementni r2 uchun sozlama bilan bir xil tarzda tavsiflang.
##### ws21 dan IP manzil yangilanishini so'rang.
- Hisobotda yangilanishdan oldin va keyin IP skrinshotlarini kiriting.
- Hisobotda ushbu nuqtada qaysi **DHCP** server parametrlaridan foydalanganingizni tasvirlab bering.

##### Virtual mashinalarning dampalarini saqlang.
**P.S. Hech qanday holatda Git-ga axlatlarni saqlamang!**

## Part 7. NAT
`-` Va nihoyat, pirojnoe ustidagi krem sifatida men sizga manzilni o'zgartirish mexanizmi haqida gapirib beraman.

**== Topshiriq ==**

*Ushbu topshiriq 5-qismdagi virtual mashinalardan foydalanadi.*
##### ws22 va r1 da */etc/apache2/ports.conf* faylida `Listen 80` qatorini `Listen 0.0.0.0:80` ga o'zgartiring, ya'ni Apache2 serverini hammaga ochiq qiling.
- Hisobotga o‘zgartirilgan fayl tarkibini aks ettiruvchi skrinshotni joylang.
##### ws22 va r1 da `service apache2 start` buyrug’I bilan Apache veb-serverini sihga tushiring.
- Hisobotda foydalanilgan buyruqning chaqiruvi va chiqishi bilan skrinshotlarni joylashtiring.
##### r2-da 4-qismdagi Faervolga o'xshash tarzda yaratilgan Faervolga quyidagi qoidalarni qo'shing:
##### 1) filter jadvalidagi qoidalarni olib tashlash - `iptables -F`;
##### 2) "NAT" jadvalidagi qoidalarni o'chirish - `iptables -F -t nat`;
##### 3) Barcha yo'naltirilgan paketlarni tashlang - `iptables --policy FORWARD DROP`.
##### Faylni 4-qismdagi kabi ishga tushiring.
##### `ping` buyrug'i bilan ws22 va r1 o'rtasidagi ulanishni tekshiring.
*Ushbu qoidalar bilan faylni ishga tushirganda, ws22 r1 bilan ping qilmasligi kerak.*
- Hisobotda foydalanilgan buyruqning chaqiruvi va chiqishi bilan skrinshotlarni joylashtiring. 
##### Faylga yana bitta qoidani qo’shing:
##### 4) Barcha ICMP protokol paketlarini marshrutlashga ruxsat bering.
##### Faylni 4-qismdagi kabi ishga tushiring.
##### Ping buyrug'i bilan ws22 va r1 o'rtasidagi ulanishni tekshiring.
*Ushbu qoidalar bilan faylni ishga tushirganda, ws22 r1 bilan ping qilishi kerak.*
- Hisobotda foydalanilgan buyruqning chaqiruvi va chiqishi bilan skrinshotlarni joylashtiring.
##### Faylga yana ikkita qoida qo'shing:
##### 5) **SNAT** yoqing, ya'ni r2 orqasida joylashgan mahalliy tarmoqdan barcha mahalliy IP-larni maskalash (5-qismdagi belgilarga muvofiq - tarmoq 10.20.0.0).
*Maslahat: Ichki paketlarni, shuningdek o'rnatilgan ulanishga ega tashqi paketlarni yo'naltirish haqida o'ylash kerak.*
##### 6) R2 mashinasining 8080-portida **DNAT** yoqing va tarmoqdan tashqaridan ws22-da ishlaydigan Apache veb-serveriga kirishni qo'shing.
*Maslahat: siz ulanishga harakat qilganingizda, ws22 va 80 port uchun mo'ljallangan yangi TCP ulanishi paydo bo'lishini hisobga olish kerak.*
- Hisobotda foydalanilgan buyruqning chaqiruvi va chiqishi bilan skrinshotlarni joylashtiring.
##### Faylni 4-qismdagi kabi ishga tushiring.
*Sinovdan oldin VirtualBox-da, agar u yoqilgan bo'lsa, NAT tarmoq interfeysini (uning mavjudligini `ip a` buyrug'i yordamida tekshirish mumkin) o'chirib qo'yish tavsiya etiladi.*
##### **SNAT** uchun TCP ulanishini tekshiring: buning uchun ws22 dan r1-dagi Apache serveriga buyruq bilan ulaning: `telnet [manzil] [port]`
##### **DNAT** uchun TCP ulanishini tekshiring: buning uchun r1 dan ws22 dagi Apache serveriga telnet buyrug'i yordamida ulaning (r2 manzili va 8080 portidan foydalaning).
- Hisobotda foydalanilgan buyruqlarning chaqiruvi va chiqishi bilan skrinshotlarni joylashtiring.

##### Virtual mashinalarning damplarini saqlang.
**P.S. Hech qanday holatda Git-ga axlatlarni saqlamang!**

## Part 8. Qo'shimcha ravishda. **SSH Tunnels** bilan tanishish

`-` Menda hammasi shu. Senda yana biron savol bormi?

`-` Ha, yana bir narsa haqida so'ramoqchi edim. Ishda kompaniyamning o‘quv loyihalari borligini kutilmaganda eshitdim. Tafsilotlarni bilmayman, lekin men, albatta, ko'rib chiqmoqchiman ... Balki foydali bo'ladi. 

`-` Haqiqatan ham qiziq, lekin bu borada sizga qanday yordam bera olaman? 

`-` Gap shundaki, ushbu loyihalarga erishish uchun siz yopiq tarmoqqa kirish huquqiga ega bo'lishingiz kerak. Bu haqda biror narsa tavsiya qila olasizmi?

`-` Albatta, berasiz... Bu yordam berishiga yuz foiz ishonchim komil emas, lekin sizga SSH tunnellari bu haqda aytib bera olaman.

**== Topshiriq ==** 

*Ushbu topshiriq 5-qismdagi virtual mashinalardan foydalanadi.*

##### r2-da 7-qismdagi qoidalar bilan xavfsizlik devorini ishga tushiring.
##### **Apache** veb-serverini ws22-da faqat localhost-da ishga tushiring (ya'ni */etc/apache2/ports.conf* faylida o'zgartiring. `Listen 80` mahalliy `Listen localhost:80`).
##### ws21-dan ws22-da veb-serverga kirish uchun ws21-dan ws22-ga mahalliy TCP yo'naltirishdan foydalaning.
##### ws11-dan ws22-dagi veb-serverga kirish uchun ws11-dan ws22-ga masofaviy TCP-ni yo'naltirishdan foydalaning.
##### Ulanish avvalgi ikkala bosqichda ham ishlaganligini tekshirish uchun ikkinchi terminalga o'ting (masalan, Alt + F2 tugmalari yordamida) va buyruqni bajaring:
`telnet 127.0.0.1 [локальный порт]`
- Hisobotda ushbu to'rtta bandni bajarish uchun zarur bo'lgan buyruqlarni tavsiflang, shuningdek, ularning chaqiruvi va chiqishining skrinshotlarini ilova qiling.

##### Virtual mashinalarning damplarini saqlang.
**P.S. Hech qachon git-ga damplarni saqlamang!**

## Chapter IV

`-` Yordamingiz uchun katta rahmat!

`-` Marhamat! Boshqaruv asoslarini eslab qolish men uchun ham foydali bo'ldi. Men yangi narsalarni o'rganishga va DevOps-ga kirishga qaror qildim.

`-` Voy! Ish topdingizmi? 

`-` Ha, ammo, ko'chib ketishga to’g’ri keladi. Shunday qilib, keyingi safar hamma narsani o'zingiz o'zlashtirishingiz kerak bo'ladi.

`-` Ertami-kechmi baribir boshlashim kerak edi, shuning uchun bu faqat yaxshilikka bo’lsa kerak. Keyin biz sizga albatta qo'ng'iroqlashamiz va muvaffaqiyatlaringiz haqida aytib berasiz! 

`-` Siz esa o’zingizniki bilan!

\> *Sebastyan bilan bir muddat mavhum mavzularda suhbatlashasiz, yoqimli musiqa tinglaysiz va buyurtma bergan ichimlikni tugatasiz, shundan so‘ng xayrlashasiz...*
