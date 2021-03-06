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

# Used HASC codes instead of ISO for regions -- couldn't find ISO 
GT_regions = [
    ((u"AV", u"Alta Verapaz"), [
        (u"CB",  u"Cahabón"),
        (u"CH",  u"Chahal"),
        (u"CC",  u"Chisec"),
        (u"CO",  u"Cobán"),
        (u"FB",  u"Fray Bartolomé de las Casas"),
        (u"LA",  u"Lanquin"),
        (u"PA",  u"Panzós"),
        (u"RX",  u"Raxruhá"),
        (u"CV",  u"San Cristóbal Verapaz"),
        (u"JC",  u"San Juan Chamelco"),
        (u"MT",  u"San Miguel Tucurú"),
        (u"PC",  u"San Pedro Carchá"),
        (u"CT",  u"Santa Catalina La Tinta"),
        (u"SC",  u"Santa Cruz Verapaz"),
        (u"SE",  u"Senahú"),
        (u"TC",  u"Tactic"),
        (u"TM",  u"Tamahú"),
        ]),

    ((u"BV", u"Baja Verapaz"), [
        (u"CU",  u"Cubulco"),
        (u"EC",  u"El Chol"),
        (u"GR",  u"Granados"),
        (u"PU",  u"Purulhá"),
        (u"RA",  u"Rabinal"),
        (u"SA",  u"Salamá"),
        (u"SJ",  u"San Jerónimo"),
        (u"MC",  u"San Miguel Chicaj"),
        ]),

    ((u"CM", u"Chimaltenango"), [
        (u"AC",  u"Acatenango"),
        (u"CH",  u"Chimaltenango"),
        (u"ET",  u"El Tejar"),
        (u"PR",  u"Parramos"),
        (u"PC",  u"Patzicía"),
        (u"PN",  u"Patzún"),
        (u"PO",  u"Pochuta"),
        (u"AI",  u"San Andrés Itzapa"),
        (u"JP",  u"San José Poaquíl"),
        (u"JC",  u"San Juan Comalapa"),
        (u"MJ",  u"San Martín Jilotepeque"),
        (u"SA",  u"Santa Apolonia"),
        (u"CB",  u"Santa Cruz Balanyá"),
        (u"TG",  u"Tecpán Guatemala"),
        (u"YE",  u"Yepocapa"),
        (u"ZA",  u"Zaragoza"),
        ]),

    ((u"CQ", u"Chiquimula"), [
        (u"CA",  u"Camotán"),
        (u"CH",  u"Chiquimula"),
        (u"CM",  u"Concepción Las Minas"),
        (u"ES",  u"Esquipulas"),
        (u"IP",  u"Ipala"),
        (u"JO",  u"Jocotán"),
        (u"OL",  u"Olopa"),
        (u"QU",  u"Quezaltepeque"),
        (u"SJ",  u"San Jacinto"),
        (u"JA",  u"San José La Arada"),
        (u"JE",  u"San Juan Ermita"),
        ]),

    ((u"PR", u"El Progreso"), [
        (u"EJ",  u"El Jícaro"),
        (u"GU",  u"Guastatoya"),
        (u"MO",  u"Morazán"),
        (u"AA",  u"San Agustín Acasaguastlán"),
        (u"AP",  u"San Antonio La Paz"),
        (u"CA",  u"San Cristóbal Acasaguastlán"),
        (u"SR",  u"Sanarate"),
        (u"SS",  u"Sansare"),
        ]),

    ((u"ES", u"Escuintla"), [
        (u"ES",  u"Escuintla"),
        (u"GU",  u"Guanagazapa"),
        (u"IZ",  u"Iztapa"),
        (u"LD",  u"La Democracia"),
        (u"LG",  u"La Gomera"),
        (u"MA",  u"Masagua"),
        (u"NC",  u"Nueva Concepción"),
        (u"PA",  u"Palín"),
        (u"SJ",  u"San José"),
        (u"VP",  u"San Vicente Pacaya"),
        (u"LC",  u"Santa Lucía Cotzumalguapa"),
        (u"SI",  u"Siquinalá"),
        (u"TI",  u"Tiquisate"),
        ]),

    ((u"GU", u"Guatemala"), [
        (u"AM",  u"Amatitlán"),
        (u"CN",  u"Chinautla"),
        (u"CR",  u"Chuarrancho"),
        (u"CG",  u"Ciudad Guatemala"),
        (u"FR",  u"Fraijanes"),
        (u"MX",  u"Mixco"),
        (u"PA",  u"Palencia"),
        (u"JP",  u"San José Pinula"),
        (u"JG",  u"San José del Golfo"),
        (u"JS",  u"San Juan Sacatepéquez"),
        (u"MP",  u"San Miguel Petapa"),
        (u"SP",  u"San Pedro Ayampuc"),
        (u"PS",  u"San Pedro Sacatepéquez"),
        (u"SR",  u"San Raimundo"),
        (u"CP",  u"Santa Catarina Pinula"),
        (u"VC",  u"Villa Canales"),
        (u"VN",  u"Villa Nueva"),
        ]),

    ((u"HU", u"Huehuetenango"), [
        (u"AG",  u"Aguacatán"),
        (u"CT",  u"Chiantla"),
        (u"CO",  u"Colotenango"),
        (u"CH",  u"Concepción Huista"),
        (u"CU",  u"Cuilco"),
        (u"HU",  u"Huehuetenango"),
        (u"IX",  u"Ixtahuacán"),
        (u"JA",  u"Jacaltenango"),
        (u"LD",  u"La Democracia"),
        (u"LL",  u"La Libertad"),
        (u"MC",  u"Malacatancito"),
        (u"NE",  u"Nentón"),
        (u"AH",  u"San Antonio Huista"),
        (u"GI",  u"San Gaspar Ixchil"),
        (u"SJ",  u"San Juan Atitán"),
        (u"JI",  u"San Juan Ixcoy"),
        (u"MI",  u"San Mateo Ixtatán"),
        (u"MA",  u"San Miguel Acatán"),
        (u"PN",  u"San Pedro Necta"),
        (u"RI",  u"San Rafael La Independencia"),
        (u"RP",  u"San Rafael Petzal"),
        (u"SS",  u"San Sebastián Coatán"),
        (u"SH",  u"San Sebastián Huehuetenango"),
        (u"SA",  u"Santa Ana Huista"),
        (u"SB",  u"Santa Bárbara"),
        (u"CB",  u"Santa Cruz Barillas"),
        (u"SE",  u"Santa Eulalia"),
        (u"SC",  u"Santiago Chimaltenango"),
        (u"SO",  u"Soloma"),
        (u"TE",  u"Tectitán"),
        (u"TS",  u"Todos Santos Cuchumatán"),
        (u"UC",  u"Unión Cantinil"),
        ]),

    ((u"IZ", u"Izabal"), [
        (u"EE",  u"El Estor"),
        (u"LI",  u"Livingston"),
        (u"LA",  u"Los Amates"),
        (u"MO",  u"Morales"),
        (u"PB",  u"Puerto Barrios"),
        ]),

    ((u"JA", u"Jalapa"), [
        (u"JA",  u"Jalapa"),
        (u"MA",  u"Mataquescuintla"),
        (u"MO",  u"Monjas"),
        (u"CA",  u"San Carlos Alzatate"),
        (u"LJ",  u"San Luis Jilotepeque"),
        (u"MC",  u"San Manuel Chaparrón"),
        (u"PP",  u"San Pedro Pinula"),
        ]),

    ((u"JU", u"Jutiapa"), [
        (u"AB",  u"Agua Blanca"),
        (u"AM",  u"Asunción Mita"),
        (u"AT",  u"Atescatempa"),
        (u"CM",  u"Comapa"),
        (u"CG",  u"Conguaco"),
        (u"EA",  u"El Adelanto"),
        (u"EP",  u"El Progreso"),
        (u"JA",  u"Jalpatagua"),
        (u"JE",  u"Jerez"),
        (u"JU",  u"Jutiapa"),
        (u"MO",  u"Moyuta"),
        (u"PA",  u"Pasaco"),
        (u"QU",  u"Quesada"),
        (u"SJ",  u"San José Acatempa"),
        (u"SC",  u"Santa Catarina Mita"),
        (u"YU",  u"Yupiltepeque"),
        (u"ZA",  u"Zapotitlán"),
        ]),

    ((u"PE", u"Petén"), [
        (u"DO",  u"Dolores"),
        (u"FL",  u"Flores"),
        (u"LL",  u"La Libertad"),
        (u"MM",  u"Melchor de Mencos"),
        (u"PO",  u"Poptún"),
        (u"SA",  u"San Andrés"),
        (u"SB",  u"San Benito"),
        (u"SF",  u"San Francisco"),
        (u"SJ",  u"San José"),
        (u"SL",  u"San Luis"),
        (u"AN",  u"Santa Ana"),
        (u"SX",  u"Sayaxché"),
        ]),

    ((u"QZ", u"Quetzaltenango"), [
        (u"AL",  u"Almolonga"),
        (u"CB",  u"Cabricán"),
        (u"CJ",  u"Cajolá"),
        (u"CT",  u"Cantel"),
        (u"CP",  u"Coatepeque"),
        (u"CM",  u"Colomba"),
        (u"CC",  u"Concepción Chiquirichapa"),
        (u"EP",  u"El Palmar"),
        (u"FC",  u"Flores Costa Cuca"),
        (u"GE",  u"Génova"),
        (u"HU",  u"Huitán"),
        (u"LE",  u"La Esperanza"),
        (u"OL",  u"Olintepeque"),
        (u"OS",  u"Ostuncalco"),
        (u"PA",  u"Palestina de Los Altos"),
        (u"QU",  u"Quetzaltenango"),
        (u"SJ",  u"Salcajá"),
        (u"CS",  u"San Carlos Sija"),
        (u"FU",  u"San Francisco La Unión"),
        (u"SS",  u"San Martín Sacatepéquez"),
        (u"SM",  u"San Mateo"),
        (u"MS",  u"San Miguel Sigüilá"),
        (u"SB",  u"Sibilia"),
        (u"ZU",  u"Zunil"),
        ]),

    ((u"QC", u"Quiché"), [
        (u"CA",  u"Canillá"),
        (u"CJ",  u"Chajul"),
        (u"CM",  u"Chicamán"),
        (u"CC",  u"Chichicastenango"),
        (u"CH",  u"Chiché"),
        (u"CQ",  u"Chinique"),
        (u"CU",  u"Cunén"),
        (u"IX",  u"Ixcán"),
        (u"JO",  u"Joyabaj"),
        (u"NE",  u"Nebaj"),
        (u"PC",  u"Pachalum"),
        (u"PZ",  u"Patzité"),
        (u"SA",  u"Sacapulas"),
        (u"AS",  u"San Andrés Sajcabajá"),
        (u"AI",  u"San Antonio Ilotenango"),
        (u"BJ",  u"San Bartolomé Jocotenango"),
        (u"JC",  u"San Juan Cotzal"),
        (u"PJ",  u"San Pedro Jocopilas"),
        (u"SC",  u"Santa Cruz del Quiché"),
        (u"US",  u"Uspantán"),
        (u"ZA",  u"Zacualpa"),
        ]),

    ((u"RE", u"Retalhuleu"), [
        (u"CH",  u"Champerico"),
        (u"EA",  u"El Asintal"),
        (u"NS",  u"Nuevo San Carlos"),
        (u"RE",  u"Retalhuleu"),
        (u"AV",  u"San Andrés Villa Seca"),
        (u"SF",  u"San Felipe"),
        (u"MZ",  u"San Martín Zapotitlán"),
        (u"SS",  u"San Sebastián"),
        (u"SC",  u"Santa Cruz Muluá"),
        ]),

    ((u"SA", u"Sacatepéquez"), [
        (u"AL",  u"Alotenango"),
        (u"AG",  u"Antigua Guatemala"),
        (u"CV",  u"Ciudad Vieja"),
        (u"JO",  u"Jocotenango"),
        (u"MM",  u"Magdalena Milpas Altas"),
        (u"PA",  u"Pastores"),
        (u"AA",  u"San Antonio Aguas Calientes"),
        (u"BM",  u"San Bartolomé Milpas Altas"),
        (u"LS",  u"San Lucas Sacatepéquez"),
        (u"MD",  u"San Miguel Dueñas"),
        (u"CB",  u"Santa Catarina Barahona"),
        (u"LM",  u"Santa Lucía Milpas Altas"),
        (u"MJ",  u"Santa María de Jesús"),
        (u"SS",  u"Santiago Sacatepéquez"),
        (u"DX",  u"Santo Domingo Xenacoj"),
        (u"SU",  u"Sumpango"),
        ]),

    ((u"SM", u"San Marcos"), [
        (u"AY",  u"Ayutla"),
        (u"CA",  u"Catarina"),
        (u"CO",  u"Comitancillo"),
        (u"CT",  u"Concepción Tutuapa"),
        (u"EQ",  u"El Quetzal"),
        (u"ER",  u"El Rodeo"),
        (u"ET",  u"El Tumbador"),
        (u"EP",  u"Esquipulas Palo Gordo"),
        (u"IX",  u"Ixchiguan"),
        (u"LR",  u"La Reforma"),
        (u"MA",  u"Malacatán"),
        (u"NP",  u"Nuevo Progreso"),
        (u"OC",  u"Ocós"),
        (u"PA",  u"Pajapita"),
        (u"RB",  u"Río Blanco"),
        (u"AS",  u"San Antonio Sacatepéquez"),
        (u"CC",  u"San Cristóbal Cucho"),
        (u"JO",  u"San José Ojetenam"),
        (u"SL",  u"San Lorenzo"),
        (u"SM",  u"San Marcos"),
        (u"MI",  u"San Miguel Ixtahuacán"),
        (u"SP",  u"San Pablo"),
        (u"PS",  u"San Pedro Sacatepéquez"),
        (u"RP",  u"San Rafaél Pie de La Cuesta"),
        (u"SB",  u"Sibinal"),
        (u"SC",  u"Sipacapa"),
        (u"TN",  u"Tacaná"),
        (u"TM",  u"Tajumulco"),
        (u"TE",  u"Tejutla"),
        ]),

    ((u"SR", u"Santa Rosa"), [
        (u"BA",  u"Barberena"),
        (u"CA",  u"Casillas"),
        (u"CH",  u"Chiquimulilla"),
        (u"CU",  u"Cuilapa"),
        (u"GU",  u"Guazacapán"),
        (u"NS",  u"Nueva Santa Rosa"),
        (u"OR",  u"Oratorio"),
        (u"PN",  u"Pueblo Nuevo Viñas"),
        (u"JT",  u"San Juan Tecuaco"),
        (u"RF",  u"San Rafaél Las Flores"),
        (u"CN",  u"Santa Cruz Naranjo"),
        (u"MI",  u"Santa María Ixhuatán"),
        (u"RL",  u"Santa Rosa de Lima"),
        (u"TA",  u"Taxisco"),
        ]),

    ((u"SO", u"Sololá"), [
        (u"CO",  u"Concepción"),
        (u"NA",  u"Nahualá"),
        (u"PA",  u"Panajachel"),
        (u"AS",  u"San Andrés Semetabaj"),
        (u"AP",  u"San Antonio Palopó"),
        (u"JC",  u"San José Chacayá"),
        (u"JL",  u"San Juan La Laguna"),
        (u"LT",  u"San Lucas Tolimán"),
        (u"ML",  u"San Marcos La Laguna"),
        (u"PL",  u"San Pablo La Laguna"),
        (u"SP",  u"San Pedro La Laguna"),
        (u"CI",  u"Santa Catarina Ixtahuacan"),
        (u"CP",  u"Santa Catarina Palopó"),
        (u"CL",  u"Santa Clara La Laguna"),
        (u"SC",  u"Santa Cruz La Laguna"),
        (u"LU",  u"Santa Lucía Utatlán"),
        (u"MV",  u"Santa María Visitación"),
        (u"SA",  u"Santiago Atitlán"),
        (u"SO",  u"Sololá"),
        ]),

    ((u"SU", u"Suchitepéquez"), [
        (u"CH",  u"Chicacao"),
        (u"CU",  u"Cuyotenango"),
        (u"MA",  u"Mazatenango"),
        (u"PA",  u"Patulul"),
        (u"PN",  u"Pueblo Nuevo"),
        (u"RB",  u"Río Bravo"),
        (u"SA",  u"Samayac"),
        (u"AS",  u"San Antonio Suchitepequez"),
        (u"SB",  u"San Bernardino"),
        (u"FZ",  u"San Francisco Zapotitlán"),
        (u"SG",  u"San Gabriel"),
        (u"JI",  u"San José El Ídolo"),
        (u"JB",  u"San Juan Bautista"),
        (u"SL",  u"San Lorenzo"),
        (u"MP",  u"San Miguel Panán"),
        (u"PJ",  u"San Pablo Jocopilas"),
        (u"BA",  u"Santa Bárbara"),
        (u"DS",  u"Santo Domingo Suchitepequez"),
        (u"TU",  u"Santo Tomas La Unión"),
        (u"ZU",  u"Zunilito"),
        ]),

    ((u"TO", u"Totonicapán"), [
        (u"MO",  u"Momostenango"),
        (u"AX",  u"San Andrés Xecul"),
        (u"SB",  u"San Bartolo"),
        (u"CT",  u"San Cristóbal Totonicapán"),
        (u"FA",  u"San Francisco El Alto"),
        (u"LR",  u"Santa Lucía La Reforma"),
        (u"MC",  u"Santa María Chiquimula"),
        (u"TO",  u"Totonicapán"),
        ]),

    ((u"ZA", u"Zacapa"), [
        (u"CA",  u"Cabañas"),
        (u"ES",  u"Estanzuela"),
        (u"GU",  u"Gualán"),
        (u"HU",  u"Huité"),
        (u"LU",  u"La Unión"),
        (u"RH",  u"Río Hondo"),
        (u"SD",  u"San Diego"),
        (u"TE",  u"Teculután"),
        (u"US",  u"Usumatlán"),
        (u"ZA",  u"Zacapa"),
        ]),
]
