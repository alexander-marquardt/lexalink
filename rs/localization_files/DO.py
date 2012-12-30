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

DO_regions = [
    ((u"DO-02", u"Azua"), [
        (u"AC",  u"Azua de Compostela"),
        (u"ES",  u"Estebania"),
        (u"GU",  u"Guayabal"),
        (u"LC",  u"Las Charcas"),
        (u"YV",  u"Las Yayas de Viajama"),
        (u"PL",  u"Padre Las Casas"),
        (u"PR",  u"Peralta"),
        (u"PV",  u"Pueblo Viejo"),
        (u"SY",  u"Sabana Yegua"),
        (u"VT",  u"Villa Tabara Arriba"),
        ]),

    ((u"DO-03", u"Bahoruco"), [
        (u"GA",  u"Galvan"),
        (u"LR",  u"Los Rios"),
        (u"NE",  u"Neyba"),
        (u"TA",  u"Tamayo"),
        (u"UV",  u"Uvilla"),
        (u"VJ",  u"Villa Jaragua"),
        ]),

    ((u"DO-04", u"Barahona"), [
        (u"CA",  u"Cabral"),
        (u"EP",  u"El Peñón"),
        (u"EN",  u"Enriquillo"),
        (u"FU",  u"Fundación"),
        (u"LC",  u"La Cienaga"),
        (u"LS",  u"Las Salinas"),
        (u"PA",  u"Paraiso"),
        (u"PO",  u"Polo"),
        (u"SC",  u"Santa Cruz de Barahona"),
        (u"VN",  u"Vicente Noble"),
        ]),

    ((u"DO-05", u"Dajabón"), [
        (u"DA",  u"Dajabón"),
        (u"EP",  u"El Pino"),
        (u"LC",  u"Loma de Cabrera"),
        (u"PA",  u"Partido"),
        (u"RE",  u"Restauración"),
        ]),

    ((u"DO-01", u"Distrito Nacional (Santo Domingo)"), [
        
        # the following codes are "invented" -- arbitrary numbers, taken from a Wikipedia page that
        # gave a listing of the "sectores" in Santo Domingo.
        (u"1",  u"24 de Abril"),
        (u"2",  u"30 de Mayo"),
        (u"3",  u"Altos de Arroyo Hondo"),
        (u"4",  u"Arroyo Manzano"),
        (u"5",  u"Atala"),
        (u"6",  u"Bella Vista"),
        (u"7",  u"Buenos Aires (Distrito Nacional)"),
        (u"8",  u"Cacique"),
        (u"9",  u"Centro de los Héroes"),
        (u"10",  u"Centro Olímpico"),
        (u"11",  u"Cerros de Arroyo Hondo"),
        (u"12",  u"Ciudad Colonial"),
        (u"13",  u"Ciudad Nueva"),
        (u"14",  u"Ciudad Universitaria"),
        (u"15",  u"Cristo Rey"),
        (u"16",  u"Domingo Sabio"),
        (u"17",  u"El Millón"),
        (u"18",  u"Ensanche Capotillo"),
        (u"19",  u"Ensanche Espaillat"),
        (u"20",  u"Ensanche La Fe"),
        (u"21",  u"Ensanche Luperón"),
        (u"22",  u"Ensanche Naco"),
        (u"23",  u"Ensanche Quisqueya"),
        (u"24",  u"Gazcue"),
        (u"25",  u"General Antonio Duverge"),
        (u"26",  u"Gualey"),
        (u"27",  u"Honduras del Norte"),
        (u"28",  u"Honduras del Oeste"),
        (u"29",  u"Jardín Botánico"),
        (u"30",  u"Jardín Zoológico"),
        (u"31",  u"Jardines del Sur"),
        (u"32",  u"Julieta Morales"),
        (u"33",  u"La Agustina"),
        (u"34",  u"La Esperilla"),
        (u"35",  u"La Hondonada"),
        (u"36",  u"La Isabela"),
        (u"37",  u"La Julia"),
        (u"38",  u"La Zurza"),
        (u"39",  u"Los Cacicazgos"),
        (u"40",  u"Los Jardines"),
        (u"41",  u"Los Peralejos"),
        (u"42",  u"Los Prados"),
        (u"43",  u"Los Restauradores"),
        (u"44",  u"Los Rios"),
        (u"45",  u"Maria Auxiliadora"),
        (u"46",  u"Mata Hambre"),
        (u"47",  u"Mejoramiento Social"),
        (u"48",  u"Mirador Norte"),
        (u"49",  u"Mirador Sur"),
        (u"50",  u"Miraflores"),
        (u"51",  u"Miramar"),
        (u"52",  u"Nuestra Señora de la Paz"),
        (u"53",  u"Nuevo Arroyo Hondo"),
        (u"54",  u"Palma Real"),
        (u"55",  u"Paraíso"),
        (u"56",  u"Paseo de los Indios"),
        (u"57",  u"Piantini"),
        (u"58",  u"Puerto Isabela"),
        (u"59",  u"Renacimiento"),
        (u"60",  u"San Carlos"),
        (u"61",  u"San Diego"),
        (u"62",  u"San Geronimo"),
        (u"63",  u"San Juan Bosco"),
        (u"64",  u"Simón Bolivar"),
        (u"65",  u"Tropical de Metaldom"),
        (u"66",  u"Viejo Arroyo Hondo"),
        (u"67",  u"Villa Agrícolas"),
        (u"68",  u"Villa Consuelo"),
        (u"69",  u"Villa Francisca"),
        (u"70",  u"Villa Juana"),
        ]),

    ((u"DO-06", u"Duarte"), [
        (u"AR",  u"Arenoso"),
        (u"CA",  u"Castillo"),
        (u"HO",  u"Hostos"),
        (u"LG",  u"Las Guaranas"),
        (u"PI",  u"Pimentel"),
        (u"SF",  u"San Francisco de Macorís"),
        (u"VR",  u"Villa Rivas"),
        ]),

    ((u"DO-08", u"El Seybo"), [
        (u"MI",  u"Miches"),
        (u"SC",  u"Santa Cruz del Seybo"),
        ]),

    ((u"DO-07", u"Elías Piña"), [
        (u"BA",  u"Banica"),
        (u"CO",  u"Comendador"),
        (u"EL",  u"El Llano"),
        (u"HV",  u"Hondo Valle"),
        (u"JS",  u"Juan Santiago"),
        (u"PS",  u"Pedro Santana"),
        ]),

    ((u"DO-09", u"Espaillat"), [
        (u"CG",  u"Cayetano Germosén"),
        (u"GH",  u"Gaspar Hernández"),
        (u"JN",  u"Jamao al Norte"),
        (u"JC",  u"José Contreras"),
        (u"MO",  u"Moca"),
        (u"SV",  u"San Victor"),
        ]),

    ((u"DO-30", u"Hato Mayor"), [
        (u"EV",  u"El Valle"),
        (u"HM",  u"Hato Mayor del Rey"),
        (u"SM",  u"Sabana de la Mar"),
        ]),

    ((u"DO-19", u"Hermanas Mirabal"), [
        (u"SA",  u"Salcedo"),
        (u"TE",  u"Tenares"),
        (u"VT",  u"Villa Tapia"),
        ]),

    ((u"DO-10", u"Independencia"), [
        (u"CR",  u"Cristobal"),
        (u"DU",  u"Duvergé"),
        (u"JI",  u"Jimaní"),
        (u"LD",  u"La Descubierta"),
        (u"ME",  u"Mella"),
        (u"PR",  u"Postrer Rio"),
        ]),

    ((u"DO-11", u"La Altagracia"), [
        (u"LN",  u"La Laguna de Nisibón"),
        (u"OB",  u"Otra Banda"),
        (u"SH",  u"Salvaleón de Higüey"),
        (u"SR",  u"San Rafael del Yuma"),
        ]),

    ((u"DO-12", u"La Romana"), [
        (u"GU",  u"Guaymate"),
        (u"LR",  u"La Romana"),
        ]),

    ((u"DO-13", u"La Vega"), [
        (u"CV",  u"Concepción de la Vega"),
        (u"CO",  u"Constanza"),
        (u"JB",  u"Jarabacoa"),
        (u"JA",  u"Jima Abajo"),
        ]),

    ((u"DO-14", u"María Trinidad Sánchez"), [
        (u"CA",  u"Cabrera"),
        (u"EF",  u"El Factor"),
        (u"NA",  u"Nagua"),
        (u"RS",  u"Rio San Juan"),
        ]),

    ((u"DO-28", u"Monseñor Nouel"), [
        (u"BO",  u"Bonao"),
        (u"MA",  u"Maimón"),
        (u"PB",  u"Piedra Blanca"),
        ]),

    ((u"DO-15", u"Monte Cristi"), [
        (u"CA",  u"Castañuela"),
        (u"GU",  u"Guayubín"),
        (u"LM",  u"Las Matas de Santa Cruz"),
        (u"PS",  u"Pepillo Salcedo"),
        (u"SF",  u"San Fernando de Monte Cristi"),
        (u"VV",  u"Villa Vázquez"),
        ]),

    ((u"DO-29", u"Monte Plata"), [
        (u"BA",  u"Bayaguana"),
        (u"DJ",  u"Don Juan"),
        (u"ES",  u"Esperalvillo"),
        (u"MP",  u"Monte Plata"),
        (u"SG",  u"Sabana Grande de Boyá"),
        (u"YA",  u"Yamasá"),
        ]),

    ((u"DO-16", u"Pedernales"), [
        (u"OV",  u"Oviedo"),
        (u"PE",  u"Pedernales"),
        ]),

    ((u"DO-17", u"Peravia"), [
        (u"BA",  u"Baní"),
        (u"MA",  u"Matanzas"),
        (u"NI",  u"Nizao"),
        (u"SB",  u"Sabana Buey"),
        (u"VF",  u"Villa Fundación"),
        ]),

    ((u"DO-18", u"Puerto Plata"), [
        (u"AL",  u"Altamira"),
        (u"GU",  u"Guananico"),
        (u"IM",  u"Imbert"),
        (u"LI",  u"La Isabela"),
        (u"LH",  u"Los Hidalgos"),
        (u"LU",  u"Luperon"),
        (u"SF",  u"San Felipe de Puerto Plata"),
        (u"SO",  u"Sosua"),
        ]),

    ((u"DO-20", u"Samaná"), [
        (u"LT",  u"Las Terrenas"),
        (u"SB",  u"Santa Bárbara de Samaná"),
        (u"SA",  u"Sánchez"),
        ]),

    ((u"DO-21", u"San Cristóbal"), [
        (u"BH",  u"Bajos de Haina"),
        (u"CG",  u"Cambita Garabito"),
        (u"LC",  u"Los Cacaos"),
        (u"NI",  u"Nigua"),
        (u"SP",  u"Sabana Grande de Palenque"),
        (u"SC",  u"San Cristóbal"),
        (u"SG",  u"San Gregorio de Yaguate"),
        (u"VA",  u"Villa Altagracia"),
        ]),

    ((u"DO-31", u"San José de Ocoa"), [
        (u"SL",  u"Sabana Larga"),
        (u"SJ",  u"San José de Ocoa"),
        ]),

    ((u"DO-22", u"San Juan"), [
        (u"BO",  u"Bohechio"),
        (u"EC",  u"El Cercado"),
        (u"JH",  u"Juan de Herrera"),
        (u"LM",  u"Las Matas de Farfan"),
        (u"SJ",  u"San Juan de la Maguana"),
        (u"VA",  u"Vallejuelo"),
        ]),

    ((u"DO-23", u"San Pedro de Macorís"), [
        (u"CO",  u"Consuelo"),
        (u"LL",  u"Los Llanos"),
        (u"QQ",  u"Quisquella"),
        (u"RS",  u"Ramón Santana"),
        (u"SP",  u"San Pedro de Macorís"),
        ]),

    ((u"DO-25", u"Santiago"), [
        (u"JA",  u"Janico"),
        (u"LM",  u"Licey al Medio"),
        (u"PG",  u"Pedro García"),
        (u"SI",  u"Sabana Iglesia"),
        (u"SJ",  u"San José de Las Matas"),
        (u"SC",  u"Santiago de los Caballeros"),
        (u"TA",  u"Tamboril"),
        (u"VB",  u"Villa Bisonó"),
        (u"VG",  u"Villa Gonzalez"),
        ]),

    ((u"DO-26", u"Santiago Rodríguez"), [
        (u"LA",  u"Los Almácigos"),
        (u"MO",  u"Monción"),
        (u"SI",  u"San Ignacio de Sabaneta"),
        ]),

    ((u"DO-32", u"Santo Domingo"), [
        (u"BC",  u"Boca Chica"),
        (u"GU",  u"Guerra"),
        (u"LV",  u"La Victoria"),
        (u"LA",  u"Los Alcarrizos"),
        (u"PB",  u"Pedro Brand"),
        (u"ES",  u"Santo Domingo Este"),
        (u"NO",  u"Santo Domingo Norte"),
        (u"OE",  u"Santo Domingo Oeste"),
        ]),

    ((u"DO-24", u"Sánchez Ramírez"), [
        (u"CE",  u"Cevicos"),
        (u"CO",  u"Cotuí"),
        (u"FA",  u"Fantino"),
        (u"LC",  u"La Cueva"),
        (u"LM",  u"La Mata"),
        ]),

    ((u"DO-27", u"Valverde"), [
        (u"ES",  u"Esperanza"),
        (u"LS",  u"Laguna Salada"),
        (u"MA",  u"Mao"),
        ]),

]
