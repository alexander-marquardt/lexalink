# -*- coding: utf-8 -*- 

################################################################################
# LexaLink Copyright information - do not remove this copyright notice
# Copyright (C) 2012 
#
# Lexalink - a free social network and dating platform for the Google App Engine. 
#
# Original author: Alexander Marquardt
# Documentation and additional information: http://www.LexaLink.com
# Git source code repository: https://github.com/lexalink/LexaLink.git 
#
# Please consider contributing your enhancements and modifications to the LexaLink community, 
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
################################################################################

DE_regions = [
    ((u"BW", u"Baden-Wurttemberg"), [
        (u"01",    u"Alb-Donau"),
        (u"02",    u"Baden-Baden"),
        (u"03",    u"Biberach"),
        (u"04",    u"Bodensee"),
        (u"05",    u"Breisgau-Hochschwarzwald"),
        (u"06",    u"Böblingen"),
        (u"07",    u"Calw"),
        (u"08",    u"Emmendingen"),
        (u"09",    u"Enz"),
        (u"10",    u"Esslingen"),
        (u"11",    u"Freiburg"),
        (u"12",    u"Freudenstadt"),
        (u"13",    u"Göppingen"),
        (u"14",    u"Heidelberg"),
        (u"15",    u"Heidenheim"),
        (u"16",    u"Heilbronn"),
        (u"18",    u"Hohenlohe"),
        (u"19",    u"Karlsruhe"),
        (u"21",    u"Konstanz (Constance)"),
        (u"22",    u"Ludwigsburg"),
        (u"23",    u"Lörrach"),
        (u"24",    u"Main-Tauber"),
        (u"25",    u"Mannheim"),
        (u"26",    u"Neckar-Odenwald-Kreis"),
        (u"27",    u"Ortenaukreis"),
        (u"28",    u"Ostalbkreis"),
        (u"29",    u"Pforzheim"),
        (u"30",    u"Rastatt"),
        (u"31",    u"Ravensburg"),
        (u"32",    u"Rems-Murr-Kreis"),
        (u"33",    u"Reutlingen"),
        (u"34",    u"Rhein-Neckar-Kreis"),
        (u"35",    u"Rottweil"),
        (u"36",    u"Schwarzwald-Baar-Kreis"),
        (u"37",    u"Schwäbisch Hall"),
        (u"38",    u"Sigmaringen"),
        (u"39",    u"Stuttgart"),
        (u"40",    u"Tuttlingen"),
        (u"41",    u"Tübingen"),
        (u"42",    u"Ulm"),
        (u"43",    u"Waldshut"),
        (u"44",    u"Zollernalbkreis"),
        ]),

    ((u"BY", u"Bayern (Bavaria)"), [
        (u"01",    u"Aichach-Friedberg"),
        (u"02",    u"Altötting"),
        (u"03",    u"Amberg-Sulzbach"),
        (u"04",    u"Ansbach"),
        (u"05",    u"Aschaffenburg"),
        (u"06",    u"Augsburg"),
        (u"07",    u"Bad Kissingen"),
        (u"08",    u"Bad Tölz-Wolfratshausen"),
        (u"09",    u"Bamberg"),
        (u"10",    u"Bayreuth"),
        (u"11",    u"Berchtesgadener Land"),
        (u"12",    u"Cham"),
        (u"13",    u"Coburg"),
        (u"14",    u"Dachau"),
        (u"15",    u"Deggendorf"),
        (u"16",    u"Dillingen"),
        (u"17",    u"Dingolfing-Landau"),
        (u"18",    u"Donau-Ries"),
        (u"19",    u"Ebersberg"),
        (u"20",    u"Eichstätt"),
        (u"21",    u"Erding"),
        (u"22",    u"Erlangen-Höchstadt"),
        (u"23",    u"Forchheim"),
        (u"24",    u"Freising"),
        (u"25",    u"Freyung-Grafenau"),
        (u"26",    u"Fürstenfeldbruck"),
        (u"27",    u"Fürth"),
        (u"28",    u"Garmisch-Partenkirchen"),
        (u"29",    u"Günzburg"),
        (u"30",    u"Hassberge"),
        (u"31",    u"Hof"),
        (u"32",    u"Kelheim"),
        (u"33",    u"Kitzingen"),
        (u"34",    u"Kronach"),
        (u"35",    u"Kulmbach"),
        (u"36",    u"Landsberg"),
        (u"37",    u"Landshut"),
        (u"38",    u"Lichtenfels"),
        (u"39",    u"Lindau"),
        (u"40",    u"Main-Spessart"),
        (u"41",    u"Miesbach"),
        (u"42",    u"Miltenberg"),
        (u"43",    u"Mühldorf"),
        (u"44",    u"München (Landkreis München)"),
        (u"45",    u"Neu-Ulm"),
        (u"46",    u"Neuburg-Schrobenhausen"),
        (u"47",    u"Neumarkt"),
        (u"48",    u"Neustadt (Aisch)-Bad Windsheim"),
        (u"49",    u"Neustadt (Waldnaab)"),
        (u"50",    u"Nürnberger Land"),
        (u"51",    u"Oberallgäu"),
        (u"52",    u"Ostallgäu"),
        (u"53",    u"Passau"),
        (u"54",    u"Pfaffenhofen"),
        (u"55",    u"Regen"),
        (u"56",    u"Regensburg"),
        (u"57",    u"Rhön-Grabfeld"),
        (u"58",    u"Rosenheim"),
        (u"59",    u"Roth"),
        (u"60",    u"Rottal-Inn"),
        (u"61",    u"Schwandorf"),
        (u"62",    u"Schweinfurt"),
        (u"63",    u"Starnberg"),
        (u"64",    u"Straubing-Bogen"),
        (u"65",    u"Tirschenreuth"),
        (u"66",    u"Traunstein"),
        (u"67",    u"Unterallgäu"),
        (u"68",    u"Weilheim-Schongau"),
        (u"69",    u"Weissenburg-Gunzenhausen"),
        (u"70",    u"Wunsiedel"),
        (u"71",    u"Würzburg"),
        ]),

    ((u"BE", u"Berlin"), [
        (u"01",    u"Charlottenburg-Wilmersdorf"),
        (u"02",    u"Friedrichshain-Kreuzberg"),
        (u"03",    u"Lichtenberg"),
        (u"04",    u"Marzahn-Hellersdorf"),
        (u"05",    u"Mitte"),
        (u"06",    u"Neukölln"),
        (u"07",    u"Pankow"),
        (u"08",    u"Reinickendorf"),
        (u"09",    u"Spandau"),
        (u"10",    u"Steglitz-Zehlendorf"),
        (u"11",    u"Tempelhof-Schöneberg"),
        (u"12",    u"Treptow-Köpenick"),
        ]),

    ((u"BB", u"Brandenburg"), [
        (u"01",    u"Barnim"),
        (u"02",    u"Brandenburg an der Havel"),
        (u"03",    u"Cottbus"),
        (u"04",    u"Dahme-Spreewald"),
        (u"05",    u"Elbe-Elster"),
        (u"06",    u"Frankfurt (Oder)"),
        (u"07",    u"Havelland"),
        (u"08",    u"Märkisch-Oderland"),
        (u"09",    u"Oberhavel"),
        (u"10",    u"Oberspreewald-Lausitz"),
        (u"11",    u"Oder-Spree"),
        (u"12",    u"Ostprignitz-Ruppin"),
        (u"13",    u"Potsdam"),
        (u"14",    u"Potsdam-Mittelmark"),
        (u"15",    u"Prignitz"),
        (u"16",    u"Spree-Neiße"),
        (u"17",    u"Teltow-Fläming"),
        (u"18",    u"Uckermark"),        
        
        ]),

    ((u"HB", u"Bremen"), [
        (u"01",    u"Bremen"),
        (u"02",    u"Bremerhaven"),        
        
        ]),

    ((u"HH", u"Hamburg"), [
        (u"01",    u"Altona"),
        (u"02",    u"Bergedorf"),
        (u"03",    u"Eimsbüttel"),
        (u"04",    u"Hamburg-Mitte"),
        (u"05",    u"Hamburg-Nord"),
        (u"06",    u"Harburg"),
        (u"07",    u"Wandsbek"),
        ]),

    ((u"HE", u"Hessen (Hesse)"), [
        (u"01",    u"Bergstraße (Heppenheim)"),
        (u"02",    u"Darmstadt"),
        (u"03",    u"Darmstadt-Dieburg (Darmstadt, Ortsteil Kranichstein"),
        (u"04",    u"Frankfurt am Main"),
        (u"05",    u"Fulda (Fulda)"),
        (u"06",    u"Gießen (Gießen)"),
        (u"07",    u"Groß-Gerau (Groß-Gerau)"),
        (u"08",    u"Hersfeld-Rotenburg (Bad Hersfeld)"),
        (u"09",    u"Hochtaunuskreis (Bad Homburg)"),
        (u"10",    u"Kassel"),
        (u"11",    u"Kassel (Kassel)"),
        (u"12",    u"Lahn-Dill-Kreis (Wetzlar)"),
        (u"13",    u"Limburg-Weilburg (Limburg)"),
        (u"14",    u"Main-Kinzig-Kreis (Gelnhausen)"),
        (u"15",    u"Main-Taunus-Kreis (Hofheim am Taunus)"),
        (u"16",    u"Marburg-Biedenkopf (Marburg)"),
        (u"17",    u"Odenwaldkreis (Erbach)"),
        (u"18",    u"Offenbach (Dietzenbach)"),
        (u"19",    u"Offenbach am Main"),
        (u"20",    u"Rheingau-Taunus-Kreis (Bad Schwalbach)"),
        (u"21",    u"Schwalm-Eder-Kreis (Homberg (Efze))"),
        (u"22",    u"Vogelsbergkreis (Lauterbach)"),
        (u"23",    u"Waldeck-Frankenberg (Korbach)"),
        (u"24",    u"Werra-Meißner-Kreis (Eschwege)"),
        (u"25",    u"Wetteraukreis (Friedberg)"),
        (u"26",    u"Wiesbaden"),        
        
        ]),


    ((u"MV", u"Mecklenburg-Vorpommern (Mecklenburg-West Pomerania)"), [
        (u"01",    u"Bad Doberan"),
        (u"02",    u"Demmin"),
        (u"03",    u"Greifswald"),
        (u"04",    u"Güstrow"),
        (u"05",    u"Ludwigslust"),
        (u"06",    u"Mecklenburg-Strelitz"),
        (u"07",    u"Müritz"),
        (u"08",    u"Neubrandenburg"),
        (u"09",    u"Nordvorpommern"),
        (u"10",    u"Nordwestmecklenburg"),
        (u"11",    u"Ostvorpommern"),
        (u"12",    u"Parchim"),
        (u"13",    u"Rostock"),
        (u"14",    u"Rügen"),
        (u"15",    u"Schwerin"),
        (u"16",    u"Stralsund"),
        (u"17",    u"Uecker-Randow"),
        (u"18",    u"Wismar"),
        ]),

    

    ((u"NI", u"Niedersachsen (Lower Saxony)"), [
        (u"01",    u"Ammerland"),
        (u"02",    u"Aurich"),
        (u"03",    u"Braunschweig"),
        (u"04",    u"Celle"),
        (u"05",    u"Cloppenburg"),
        (u"06",    u"Cuxhaven"),
        (u"07",    u"Delmenhorst"),
        (u"08",    u"Diepholz"),
        (u"09",    u"Emden"),
        (u"10",    u"Emsland"),
        (u"11",    u"Friesland"),
        (u"12",    u"Gifhorn"),
        (u"13",    u"Goslar"),
        (u"14",    u"Grafschaft Bentheim"),
        (u"15",    u"Göttingen"),
        (u"17",    u"Hamelin-Pyrmont"),
        (u"18",    u"Hannover"),
        (u"20",    u"Harburg"),
        (u"21",    u"Helmstedt"),
        (u"22",    u"Hildesheim"),
        (u"23",    u"Holzminden"),
        (u"24",    u"Leer"),
        (u"25",    u"Lüchow-Dannenberg"),
        (u"26",    u"Lüneburg"),
        (u"27",    u"Nienburg"),
        (u"28",    u"Northeim"),
        (u"29",    u"Oldenburg"),
        (u"31",    u"Osnabrück"),
        (u"33",    u"Osterholz"),
        (u"34",    u"Osterode"),
        (u"35",    u"Peine"),
        (u"36",    u"Rotenburg (Wümme)"),
        (u"37",    u"Salzgitter"),
        (u"38",    u"Schaumburg"),
        (u"39",    u"Soltau-Fallingbostel"),
        (u"40",    u"Stade"),
        (u"41",    u"Uelzen"),
        (u"42",    u"Vechta"),
        (u"43",    u"Verden"),
        (u"44",    u"Wesermarsch"),
        (u"45",    u"Wilhelmshaven"),
        (u"46",    u"Wittmund"),
        (u"47",    u"Wolfenbüttel"),
        (u"48",    u"Wolfsburg"),
        ]),    
    
    ((u"NW", u"Nordrhein-Westfalen (North Rhine-Westphalia)"), [
        (u"01",    u"Aachen"),
        (u"02",    u"Aachen"),
        (u"03",    u"Bergischer Kreis"),
        (u"04",    u"Bielefeld"),
        (u"05",    u"Bochum"),
        (u"06",    u"Bonn"),
        (u"07",    u"Borken"),
        (u"08",    u"Bottrop"),
        (u"09",    u"Coesfeld"),
        (u"10",    u"Cologne/Köln"),
        (u"11",    u"Dortmund"),
        (u"12",    u"Duisburg"),
        (u"13",    u"Düren"),
        (u"14",    u"Düsseldorf"),
        (u"15",    u"Ennepe-Ruhr-Kreis"),
        (u"16",    u"Essen"),
        (u"17",    u"Euskirchen"),
        (u"18",    u"Gelsenkirchen"),
        (u"19",    u"Gütersloh"),
        (u"20",    u"Hagen"),
        (u"21",    u"Hamm"),
        (u"22",    u"Heinsberg"),
        (u"23",    u"Herford"),
        (u"24",    u"Herne"),
        (u"25",    u"Hochsauerlandkreis"),
        (u"26",    u"Höxter"),
        (u"27",    u"Kleve"),
        (u"28",    u"Krefeld"),
        (u"29",    u"Leverkusen"),
        (u"30",    u"Lippe"),
        (u"31",    u"Mettmann"),
        (u"32",    u"Minden-Lübbecke"),
        (u"33",    u"Märkischer Kreis"),
        (u"34",    u"Mönchengladbach"),
        (u"35",    u"Mülheim"),
        (u"36",    u"Münster"),
        (u"37",    u"Oberbergischer Kreis"),
        (u"38",    u"Oberhausen"),
        (u"39",    u"Olpe"),
        (u"40",    u"Paderborn"),
        (u"41",    u"Recklinghausen"),
        (u"42",    u"Remscheid"),
        (u"43",    u"Rhein-Erft-Kreis"),
        (u"44",    u"Rhein-Kreis Neuss"),
        (u"45",    u"Rhein-Sieg-Kreis"),
        (u"46",    u"Rheinisch-"),
        (u"47",    u"Siegen-Wittgenstein"),
        (u"48",    u"Soest"),
        (u"49",    u"Solingen"),
        (u"50",    u"Steinfurt"),
        (u"51",    u"Unna"),
        (u"52",    u"Viersen"),
        (u"53",    u"Warendorf"),
        (u"54",    u"Wesel"),
        (u"55",    u"Wuppertal"),
        ]),

    ((u"RP", u"Rheinland-Pfalz (Rhineland-Palatinate)"), [
        (u"01",    u"Ahrweiler"),
        (u"02",    u"Altenkirchen"),
        (u"03",    u"Alzey-Worms"),
        (u"04",    u"Bad Dürkheim"),
        (u"05",    u"Bad Kreuznach"),
        (u"06",    u"Bernkastel-Wittlich"),
        (u"07",    u"Birkenfeld"),
        (u"08",    u"Bitburg-Prüm"),
        (u"09",    u"Cochem-Zell"),
        (u"10",    u"Donnersbergkreis"),
        (u"11",    u"Frankenthal"),
        (u"12",    u"Germersheim"),
        (u"13",    u"Kaiserslautern"),
        (u"15",    u"Koblenz Coblenz"),
        (u"16",    u"Kusel"),
        (u"17",    u"Landau"),
        (u"18",    u"Ludwigshafen (Rheinpfalz-Kreis)"),
        (u"19",    u"Mainz"),
        (u"20",    u"Mainz-Bingen"),
        (u"21",    u"Mayen-Koblenz"),
        (u"22",    u"Neustadt (Weinstraße)"),
        (u"23",    u"Neuwied"),
        (u"24",    u"Pirmasens"),
        (u"25",    u"Rhein-Hunsrück"),
        (u"26",    u"Rhein-Lahn"),
        (u"27",    u"Rhein-Pfalz-Kreis"),
        (u"28",    u"Speyer Spires"),
        (u"29",    u"Südliche Weinstraße"),
        (u"30",    u"Südwestpfalz"),
        (u"31",    u"Trier"),
        (u"32",    u"Trier-Saarburg"),
        (u"33",    u"Vulkaneifel"),
        (u"34",    u"Westerwaldkreis"),
        (u"35",    u"Worms"),
        (u"36",    u"Zweibrücken"),
        ]),

    ((u"SL", u"Saarland"), [
        (u"01",    u"Merzig-Wadern"),
        (u"02",    u"Neunkirchen"),
        (u"03",    u"Saarbrücken"),
        (u"04",    u"Saarlouis"),
        (u"05",    u"Saarpfalz"),
        (u"06",    u"Sankt Wendel"),
        ]),

    ((u"SN", u"Sachsen (Saxony)"), [
        (u"01",    u"Bautzen"),
        (u"02",    u"Chemnitz"),
        (u"03",    u"Dresden"),
        (u"04",    u"Erzgebirgskreis"),
        (u"05",    u"Görlitz"),
        (u"07",    u"Leipzig"),
        (u"08",    u"Meißen (Meissen)"),
        (u"09",    u"Mittelsachsen"),
        (u"10",    u"Nordsachsen"),
        (u"11",    u"Sächsische Schweiz-Osterzgebirge"),
        (u"12",    u"Vogtlandkreis"),
        (u"13",    u"Zwickau"),                
        ]),

    ((u"ST", u"Sachsen-Anhalt (Saxony-Anhalt)"), [
        (u"01",    u"Altmarkkreis Salzwedel"),
        (u"02",    u"Anhalt-Bitterfeld"),
        (u"03",    u"Burgenlandkreis"),
        (u"04",    u"Börde"),
        (u"05",    u"Dessau-Roßlau"),
        (u"06",    u"Halle (Saale)"),
        (u"07",    u"Harz"),
        (u"08",    u"Jerichower Land"),
        (u"09",    u"Magdeburg"),
        (u"10",    u"Mansfeld-Südharz"),
        (u"11",    u"Saalekreis"),
        (u"12",    u"Salzlandkreis"),
        (u"13",    u"Stendal"),
        (u"14",    u"Wittenberg"),
        ]),

    ((u"SH", u"Schleswig-Holstein"), [
        (u"01",    u"Dithmarschen"),
        (u"02",    u"Flensburg"),
        (u"03",    u"Hansestadt"),
        (u"04",    u"Kiel"),
        (u"05",    u"Lauenburg"),
        (u"06",    u"Neumünster"),
        (u"07",    u"Nordfriesland"),
        (u"08",    u"Ostholstein"),
        (u"09",    u"Pinneberg"),
        (u"10",    u"Plön"),
        (u"11",    u"Rendsburg-Eckernförde"),
        (u"12",    u"Schleswig-Flensburg"),
        (u"13",    u"Segeberg"),
        (u"14",    u"Steinburg"),
        (u"15",    u"Stormarn"),        
        ]),

    ((u"TH", u"Thüringen (Thuringia)"), [
        (u"01",    u"Altenburger Land"),
        (u"02",    u"Eichsfeld"),
        (u"03",    u"Eisenach"),
        (u"04",    u"Erfurt"),
        (u"05",    u"Gera"),
        (u"06",    u"Gotha"),
        (u"07",    u"Greiz"),
        (u"08",    u"Hildburghausen"),
        (u"09",    u"Ilm-Kreis"),
        (u"10",    u"Jena"),
        (u"11",    u"Kyffhäuserkreis"),
        (u"12",    u"Nordhausen"),
        (u"13",    u"Saale-Holzland"),
        (u"14",    u"Saale-Orla"),
        (u"15",    u"Saalfeld-Rudolstadt"),
        (u"16",    u"Schmalkalden-Meiningen"),
        (u"17",    u"Sonneberg"),
        (u"18",    u"Suhl"),
        (u"19",    u"Sömmerda"),
        (u"20",    u"Unstrut-Hainich"),
        (u"21",    u"Wartburgkreis"),
        (u"22",    u"Weimar"),
        (u"23",    u"Weimarer Land"),
        ]),

]