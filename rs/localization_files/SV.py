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

# Note: I used HASC codes for these regions, as I could not find ISO codes.
SV_regions = [
    ((u"AH", u"Ahuachapán"), [
        (u"AH",  u"Ahuachapán"),
        (u"AP",  u"Apaneca"),
        (u"AT",  u"Atiquizaya"),
        (u"CA",  u"Concepción de Ataco"),
        (u"ER",  u"El Refugio"),
        (u"GU",  u"Guaymango"),
        (u"JU",  u"Jujutla"),
        (u"SF",  u"San Francisco Menéndez"),
        (u"SL",  u"San Lorenzo"),
        (u"SP",  u"San Pedro Puxtla"),
        (u"TA",  u"Tacuba"),
        (u"TU",  u"Turín"),
        ]),

    ((u"CA", u"Cabañas"), [
        (u"CI",  u"Cinquera"),
        (u"DO",  u"Dolores"),
        (u"GU",  u"Guacotecti"),
        (u"IL",  u"Ilobasco"),
        (u"JU",  u"Jutiapa"),
        (u"SI",  u"San Isidro"),
        (u"SE",  u"Sensuntepeque"),
        (u"TE",  u"Tejutepeque"),
        (u"VI",  u"Victoria"),
        ]),

    ((u"CH", u"Chalatenango"), [
        (u"AC",  u"Agua Caliente"),
        (u"AR",  u"Arcatao"),
        (u"AZ",  u"Azacualpa"),
        (u"CH",  u"Chalatenango"),
        (u"CI",  u"Citalá"),
        (u"CO",  u"Comalapa"),
        (u"CQ",  u"Concepción Quezaltepeque"),
        (u"DN",  u"Dulce Nombre de María"),
        (u"EC",  u"El Carrizal"),
        (u"EP",  u"El Paraíso"),
        (u"LL",  u"La Laguna"),
        (u"LP",  u"La Palma"),
        (u"LR",  u"La Reina"),
        (u"LV",  u"Las Vueltas"),
        (u"NJ",  u"Nombre de Jesús"),
        (u"NC",  u"Nueva Concepción"),
        (u"NT",  u"Nueva Trinidad"),
        (u"OA",  u"Ojos de Agua"),
        (u"PO",  u"Potonico"),
        (u"SO",  u"San Antonio Los Ranchos"),
        (u"SA",  u"San Antonio de la Cruz"),
        (u"SD",  u"San Fernando"),
        (u"SF",  u"San Francisco Lempa"),
        (u"SZ",  u"San Francisco Morazán"),
        (u"SI",  u"San Ignacio"),
        (u"SB",  u"San Isidro Labrador"),
        (u"SC",  u"San José Cancasque"),
        (u"SJ",  u"San José Las Flores"),
        (u"SL",  u"San Luis del Carmen"),
        (u"SM",  u"San Miguel de Mercedes"),
        (u"SR",  u"San Rafael"),
        (u"ST",  u"Santa Rita"),
        (u"TE",  u"Tejutla"),
        ]),

    ((u"CU", u"Cuscatlán"), [
        (u"CA",  u"Candelaria"),
        (u"CO",  u"Cojutepeque"),
        (u"EC",  u"El Carmen"),
        (u"ER",  u"El Rosario"),
        (u"MS",  u"Monte San Juan"),
        (u"OC",  u"Oratorio de Concepción"),
        (u"SB",  u"San Bartolomé Perulapía"),
        (u"SC",  u"San Cristóbal"),
        (u"SJ",  u"San José Guayabal"),
        (u"SP",  u"San Pedro Perulapán"),
        (u"SF",  u"San Rafael Cedros"),
        (u"SR",  u"San Ramón"),
        (u"SA",  u"Santa Cruz Analquito"),
        (u"SM",  u"Santa Cruz Michapa"),
        (u"SU",  u"Suchitoto"),
        (u"TE",  u"Tenancingo"),
        ]),

    ((u"LI", u"La Libertad"), [
        (u"AC",  u"Antiguo Cuscatlán"),
        (u"CH",  u"Chiltiupán"),
        (u"CA",  u"Ciudad Arce"),
        (u"CL",  u"Colón"),
        (u"CM",  u"Comasagua"),
        (u"HU",  u"Huizúcar"),
        (u"JA",  u"Jayaque"),
        (u"JI",  u"Jicalapa"),
        (u"LL",  u"La Libertad"),
        (u"NS",  u"Nueva San Salvador"),
        (u"NC",  u"Nuevo Cuscatlán"),
        (u"OP",  u"Opico"),
        (u"QU",  u"Quezaltepeque"),
        (u"SA",  u"Sacacoyo"),
        (u"SJ",  u"San José Villanueva"),
        (u"SM",  u"San Matías"),
        (u"SP",  u"San Pablo Tacachico"),
        (u"TL",  u"Talnique"),
        (u"TM",  u"Tamanique"),
        (u"TT",  u"Teotepeque"),
        (u"TP",  u"Tepecoyo"),
        (u"ZA",  u"Zaragoza"),
        ]),

    ((u"PA", u"La Paz"), [
        (u"CU",  u"Cuyultitán"),
        (u"EL",  u"El Rosario"),
        (u"JE",  u"Jerusalén"),
        (u"MC",  u"Mercedes La Ceiba"),
        (u"OL",  u"Olocuilta"),
        (u"PO",  u"Paraíso de Osorio"),
        (u"SA",  u"San Antonio Masahuat"),
        (u"SE",  u"San Emigdio"),
        (u"SF",  u"San Francisco Chinameca"),
        (u"SN",  u"San Juan Nonualco"),
        (u"SU",  u"San Juan Talpa"),
        (u"SJ",  u"San Juan Tepezontes"),
        (u"SH",  u"San Luis La Herradura"),
        (u"SL",  u"San Luis Talpa"),
        (u"SZ",  u"San Miguel Tepezontes"),
        (u"SM",  u"San Pedro Masahuat"),
        (u"SP",  u"San Pedro Nonualco"),
        (u"SR",  u"San Rafael Obrajuelo"),
        (u"SO",  u"Santa María Ostuma"),
        (u"ST",  u"Santiago Nonualco"),
        (u"TA",  u"Tapalhuaca"),
        (u"ZA",  u"Zacatecoluca"),
        ]),

    ((u"UN", u"La Unión"), [
        (u"AN",  u"Anamorós"),
        (u"BO",  u"Bolívar"),
        (u"CO",  u"Concepción de Oriente"),
        (u"CG",  u"Conchagua"),
        (u"EC",  u"El Carmen"),
        (u"ES",  u"El Sauce"),
        (u"IN",  u"Intipucá"),
        (u"LU",  u"La Unión"),
        (u"LI",  u"Lislique"),
        (u"MG",  u"Meanguera del Golfo"),
        (u"NE",  u"Nueva Esparta"),
        (u"PA",  u"Pasaquina"),
        (u"PO",  u"Polorós"),
        (u"SA",  u"San Alejo"),
        (u"SJ",  u"San José"),
        (u"SR",  u"Santa Rosa de Lima"),
        (u"YA",  u"Yayantique"),
        (u"YU",  u"Yucuaiquín"),
        ]),

    ((u"MO", u"Morazán"), [
        (u"AR",  u"Arambala"),
        (u"CA",  u"Cacaopera"),
        (u"CH",  u"Chilanga"),
        (u"CO",  u"Corinto"),
        (u"DC",  u"Delicias de Concepción"),
        (u"ED",  u"El Divisadero"),
        (u"ER",  u"El Rosario"),
        (u"GL",  u"Gualococti"),
        (u"GT",  u"Guatajiagua"),
        (u"JT",  u"Joateca"),
        (u"JQ",  u"Jocoaitique"),
        (u"JR",  u"Jocoro"),
        (u"LO",  u"Lolotiquillo"),
        (u"ME",  u"Meanguera"),
        (u"OS",  u"Osicala"),
        (u"PE",  u"Perquín"),
        (u"SC",  u"San Carlos"),
        (u"SF",  u"San Fernando"),
        (u"SG",  u"San Francisco Gotera"),
        (u"SI",  u"San Isidro"),
        (u"SS",  u"San Simón"),
        (u"SE",  u"Sensembra"),
        (u"SO",  u"Sociedad"),
        (u"TO",  u"Torola"),
        (u"YA",  u"Yamabal"),
        (u"YO",  u"Yoloaiquín"),
        ]),

    ((u"SM", u"San Miguel"), [
        (u"CA",  u"Carolina"),
        (u"CP",  u"Chapeltique"),
        (u"CM",  u"Chinameca"),
        (u"CR",  u"Chirilagua"),
        (u"CB",  u"Ciudad Barrios"),
        (u"CO",  u"Comacarán"),
        (u"ET",  u"El Tránsito"),
        (u"LO",  u"Lolotique"),
        (u"MO",  u"Moncagua"),
        (u"NG",  u"Nueva Guadalupe"),
        (u"NE",  u"Nuevo Edén de San Juan"),
        (u"QU",  u"Quelepa"),
        (u"SA",  u"San Antonio"),
        (u"SG",  u"San Gerardo"),
        (u"SJ",  u"San Jorge"),
        (u"SL",  u"San Luis de la Reina"),
        (u"SM",  u"San Miguel"),
        (u"SR",  u"San Rafael"),
        (u"SE",  u"Sesori"),
        (u"UL",  u"Uluazapa"),
        ]),

    ((u"SS", u"San Salvador"), [
        (u"AG",  u"Aguilares"),
        (u"AP",  u"Apopa"),
        (u"AY",  u"Ayutuxtepeque"),
        (u"CU",  u"Cuscatancingo"),
        (u"DE",  u"Delgado"),
        (u"EL",  u"El Paisnal"),
        (u"GU",  u"Guazapa"),
        (u"IL",  u"Ilopango"),
        (u"ME",  u"Mejicanos"),
        (u"NE",  u"Nejapa"),
        (u"PA",  u"Panchimalco"),
        (u"RM",  u"Rosario de Mora"),
        (u"SM",  u"San Marcos"),
        (u"SN",  u"San Martín"),
        (u"SS",  u"San Salvador"),
        (u"SG",  u"Santiago Texacuangos"),
        (u"ST",  u"Santo Tomás"),
        (u"SO",  u"Soyapango"),
        (u"TO",  u"Tonacatepeque"),
        ]),

    ((u"SV", u"San Vicente"), [
        (u"AP",  u"Apastepeque"),
        (u"GU",  u"Guadalupe"),
        (u"SY",  u"San Cayetano Istepeque"),
        (u"SE",  u"San Esteban Catarina"),
        (u"SI",  u"San Ildefonso"),
        (u"SL",  u"San Lorenzo"),
        (u"SS",  u"San Sebastián"),
        (u"SV",  u"San Vicente"),
        (u"SC",  u"Santa Clara"),
        (u"SD",  u"Santo Domingo"),
        (u"TC",  u"Tecoluca"),
        (u"TP",  u"Tepetitán"),
        (u"VE",  u"Verapaz"),
        ]),

    ((u"SA", u"Santa Ana"), [
        (u"CF",  u"Candelaria de la Frontera"),
        (u"CH",  u"Chalchuapa"),
        (u"CO",  u"Coatepeque"),
        (u"EC",  u"El Congo"),
        (u"EL",  u"El Porvenir"),
        (u"MA",  u"Masahuat"),
        (u"ME",  u"Metapán"),
        (u"SP",  u"San Antonio Pajonal"),
        (u"SS",  u"San Sebastián Salitrillo"),
        (u"SA",  u"Santa Ana"),
        (u"SR",  u"Santa Rosa Guachipilín"),
        (u"SF",  u"Santiago de la Frontera"),
        (u"TE",  u"Texistepeque"),
        ]),

    ((u"SO", u"Sonsonate"), [
        (u"AC",  u"Acajutla"),
        (u"AR",  u"Armenia"),
        (u"CA",  u"Caluco"),
        (u"CU",  u"Cuisnahuat"),
        (u"IZ",  u"Izalco"),
        (u"JU",  u"Juayúa"),
        (u"NZ",  u"Nahuizalco"),
        (u"NL",  u"Nahulingo"),
        (u"SL",  u"Salcoatitán"),
        (u"SA",  u"San Antonio del Monte"),
        (u"SJ",  u"San Julián"),
        (u"SC",  u"Santa Catarina Masahuat"),
        (u"SI",  u"Santa Isabel Ishuatán"),
        (u"SD",  u"Santo Domingo"),
        (u"SO",  u"Sonsonate"),
        (u"SZ",  u"Sonzacate"),
        ]),

    ((u"US", u"Usulután"), [
        (u"AL",  u"Alegría"),
        (u"BE",  u"Berlín"),
        (u"CA",  u"California"),
        (u"CB",  u"Concepción Batres"),
        (u"ET",  u"El Triunfo"),
        (u"ER",  u"Ereguayquín"),
        (u"ES",  u"Estanzuelas"),
        (u"JI",  u"Jiquilisco"),
        (u"JP",  u"Jucuapa"),
        (u"JR",  u"Jucuarán"),
        (u"MU",  u"Mercedes Umaña"),
        (u"NG",  u"Nueva Granada"),
        (u"OZ",  u"Ozatlán"),
        (u"PT",  u"Puerto El Triunfo"),
        (u"SA",  u"San Agustín"),
        (u"SB",  u"San Buenaventura"),
        (u"SD",  u"San Dionisio"),
        (u"SF",  u"San Francisco Javier"),
        (u"SE",  u"Santa Elena"),
        (u"SM",  u"Santa María"),
        (u"SG",  u"Santiago de María"),
        (u"TE",  u"Tecapán"),
        (u"US",  u"Usulután"),
        ]),

]
