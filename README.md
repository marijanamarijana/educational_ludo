# EDUCATIONAL LUDO (EN)

---

**Educational Ludo** is a multiplayer board game for kids or adults that combines the classic Ludo gameplay with fun educational questions.  
Players compete to reach the finish first while answering quiz questions that test their knowledge and add an extra challenge to every move.
Play with up to 4 friends per game, whether you choose the Macedonian or English version it's all up to you! 

The game is designed for:
- Playing with friends 
- Learning through interactive multiple-choice and true/false questions
- Enjoying a colorful and simple user interface built with Python and Pygame

What separates it from a classic Ludo is:
- While playing you can click on the QUIZ button that will prompt you to pick a number between 1-6 which will then (let's say u selected 4) if answering correctly move u up 4 tiles but if answering wrong your pawn will be moved 4 tiles backwards
- If u and an opponent both are on a tile - a DUEL occurs, you and your opponent answer questions as fast and as correctly as you can. The person with the most correctly answered questions in the short amount of time WINS the duel and stays on the tile, the losing pawn returns to it's home base 

---

The game can also be downloaded and played with friends as a standalone **.exe** file (check the Releases - you can download it from there). If you run into any issues when running the game try disabling your antivirus.

**You can preview the user interface and gameplay inside the demo folder [here](https://github.com/marijanamarijana/educational_ludo/tree/main/demo).**

---

To start the multiplayer ludo game *LOCALY* on your machine in console / terminal, run the following commands:
1. **python server_tcp.py**
2. **python client_tcp.py** (run it in 2 separate terminals for 2 players - you should have something like on the picture -
   for 3 players you should have 3 consoles with **python client_tcp.py** and one with  **python server_tcp.py**)
<img width="553" height="101" alt="image" src="https://github.com/user-attachments/assets/85cf5b82-e3fe-44cb-a256-319a156a50ba" />

----

To start the multiplayer ludo *ON THE CLOUD* (on a hosted server) on your machine in the client_tcp.py file uncomment the settings for 
the host and start it with the command **python client_tcp.py**. You can also start as many clients as u like here - starting the client is the same as it is locally and the server is already provided for you.



# ЕДУКАЦИСКО НЕ ЛУТИ СЕ ЧОВЕЧЕ (МК)

---

**Едукациско не лути се човече** е игра за повеќе играчи за деца и возрасни која ја комбинира класичната игра „Не лути се човече“ со забавни едукативни прашања.
Играчите се натпреваруваат кој прв ќе стигне до целта, додека одговараат на прашања што го тестираат нивното знаење.
Може да се игра со најмногу 4 пријатели во една игра, а дали ќе ја играте македонската или англиската верзија – изборот е ваш!

Играта е наменета за:
- Играње со пријатели
- Учење преку интерактивни прашања со повеќекратен избор и точно/неточно
- Уживање во шарен и едноставен кориснички интерфејс изработен со Python и Pygame

Она што ја разликува од класичната Не лути се човече е:
- Додека играте, можете да кликнете на копчето КВИЗ, по што ќе треба да изберете број од 1-6.
Доколку (на пример) изберете 4 и одговорите точно, ќе се придвижите 4 полиња напред;
ако одговорите погрешно, вашата фигура ќе се помести 4 полиња наназад.
- Доколку вие и противникот се најдете на исто поле – се случува ДУЕЛ.
Вие и противникот одговарате на прашања што е можно побрзо и поточно.
Играчот со најмногу точно одговорени прашања во краткиот временски период е победник на дуелот и останува на полето,
додека фигурата на поразениот се враќа во почетната база.

---

Играта може да се преземе и да се игра со пријатели како самостојна **.exe** датотека
(видете во Releases – од таму може да се преземе).
Доколку наидете на проблем при стартување на играта, обидете се да го исклучите антивирусот.

**Може да го прегледате корисничкиот интерфејс и играта во демо-папката [тука](https://github.com/marijanamarijana/educational_ludo/tree/main/demo).**

---

За да ја стартувате мултиплеер Лудо играта *ЛОКАЛНО* на вашиот компјутер преку конзола / терминал, извршете ги следните команди:
1. **python server_tcp.py**
2. **python client_tcp.py** (стартувајте го во 2 одделни терминали за 2 играчи – треба да добиете изглед како на сликата.
За 3 играчи ќе имате 3 различни конзоли со python client_tcp.py и една со python server_tcp.py.)
<img width="553" height="101" alt="image" src="https://github.com/user-attachments/assets/85cf5b82-e3fe-44cb-a256-319a156a50ba" />

----

За да ја стартувате мултиплеер Не лути се човече играта *НА CLOUD* (на хостиран сервер) на вашиот компјутер,
во датотеката client_tcp.py откоментирајте ги поставките за host и стартувајте со командата
**python client_tcp.py.**
И тука можете да стартувате онолку клиенти колку што сакате – стартувањето на клиентот е исто како и локално,
а серверот веќе е обезбеден за вас.
