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

FR_regions = [
    ((u"A", u"Alsace"), [
        (u"BR",  u"Bas-Rhin"),
        (u"HR",  u"Haut-Rhin"),
        ]),

    ((u"B", u"Aquitaine"), [
        (u"DD",  u"Dordogne"),
        (u"GI",  u"Gironde"),
        (u"LD",  u"Landes"),
        (u"LG",  u"Lot-et-Garonne"),
        (u"PA",  u"Pyrénées-Atlantiques"),
        ]),

    ((u"C", u"Auvergne"), [
        (u"AL",  u"Allier"),
        (u"CL",  u"Cantal"),
        (u"HL",  u"Haute-Loire"),
        (u"PD",  u"Puy-de-Dôme"),
        ]),

    ((u"P", u"Basse-Normandie"), [
        (u"CV",  u"Calvados"),
        (u"MH",  u"Manche"),
        (u"OR",  u"Orne"),
        ]),

    ((u"D", u"Bourgogne"), [
        (u"CO",  u"Côte-d'Or"),
        (u"NI",  u"Nièvre"),
        (u"SL",  u"Saône-et-Loire"),
        (u"YO",  u"Yonne"),
        ]),

    ((u"E", u"Bretagne"), [
        (u"CA",  u"Côtes-d'Armor"),
        (u"FI",  u"Finistère"),
        (u"IV",  u"Ille-et-Vilaine"),
        (u"MB",  u"Morbihan"),
        ]),

    ((u"F", u"Centre"), [
        (u"CH",  u"Cher"),
        (u"EL",  u"Eure-et-Loir"),
        (u"IN",  u"Indre"),
        (u"IL",  u"Indre-et-Loire"),
        (u"LC",  u"Loir-et-Cher"),
        (u"LT",  u"Loiret"),
        ]),

    ((u"G", u"Champagne-Ardenne"), [
        (u"AN",  u"Ardennes"),
        (u"AB",  u"Aube"),
        (u"HM",  u"Haute-Marne"),
        (u"MR",  u"Marne"),
        ]),

    ((u"H", u"Corse"), [
        (u"CS",  u"Corse-du-Sud"),
        (u"HC",  u"Haute-Corse"),
        ]),

    ((u"I", u"Franche-Comté"), [
        (u"DB",  u"Doubs"),
        (u"HN",  u"Haute-Saône"),
        (u"JU",  u"Jura"),
        (u"TB",  u"Territoire de Belfort"),
        ]),

    ((u"Q", u"Haute-Normandie"), [
        (u"EU",  u"Eure"),
        (u"SM",  u"Seine-Maritime"),
        ]),

    ((u"J", u"Île-de-France"), [
        (u"ES",  u"Essonne"),
        (u"HD",  u"Hauts-de-Seine"),
        (u"SS",  u"Seine-Saint-Denis"),
        (u"SE",  u"Seine-et-Marne"),
        (u"VO",  u"Val-d'Oise"),
        (u"VM",  u"Val-de-Marne"),
        (u"VP",  u"Ville de Paris"),
        (u"YV",  u"Yvelines"),
        ]),
    
    
    ((u"K", u"Languedoc-Roussillon"), [
        (u"AD",  u"Aude"),
        (u"GA",  u"Gard"),
        (u"HE",  u"Hérault"),
        (u"LZ",  u"Lozère"),
        (u"PO",  u"Pyrénées-Orientales"),
        ]),

    ((u"L", u"Limousin"), [
        (u"CZ",  u"Corrèze"),
        (u"CR",  u"Creuse"),
        (u"HV",  u"Haute-Vienne"),
        ]),

    ((u"M", u"Lorraine"), [
        (u"MM",  u"Meurthe-et-Moselle"),
        (u"MS",  u"Meuse"),
        (u"MO",  u"Moselle"),
        (u"VG",  u"Vosges"),
        ]),

    ((u"N", u"Midi-Pyrénées"), [
        (u"AG",  u"Ariège"),
        (u"AV",  u"Aveyron"),
        (u"GE",  u"Gers"),
        (u"HG",  u"Haute-Garonne"),
        (u"HP",  u"Hautes-Pyrénées"),
        (u"LO",  u"Lot"),
        (u"TA",  u"Tarn"),
        (u"TG",  u"Tarn-et-Garonne"),
        ]),

    ((u"O", u"Nord-Pas-de-Calais"), [
        (u"NO",  u"Nord"),
        (u"PC",  u"Pas-de-Calais"),
        ]),

    ((u"R", u"Pays de la Loire"), [
        (u"LA",  u"Loire-Atlantique"),
        (u"ML",  u"Maine-et-Loire"),
        (u"MY",  u"Mayenne"),
        (u"ST",  u"Sarthe"),
        (u"VD",  u"Vendée"),
        ]),

    ((u"S", u"Picardie"), [
        (u"AS",  u"Aisne"),
        (u"OI",  u"Oise"),
        (u"SO",  u"Somme"),
        ]),

    ((u"T", u"Poitou-Charentes"), [
        (u"CT",  u"Charente"),
        (u"CM",  u"Charente-Maritime"),
        (u"DS",  u"Deux-Sèvres"),
        (u"VN",  u"Vienne"),
        ]),

    ((u"U", u"Provence-Alpes-Côte-d'Azur"), [
        (u"AM",  u"Alpes-Maritimes"),
        (u"AP",  u"Alpes-de-Haute-Provence"),
        (u"BD",  u"Bouches-du-Rhône"),
        (u"HA",  u"Hautes-Alpes"),
        (u"VR",  u"Var"),
        (u"VC",  u"Vaucluse"),
        ]),

    ((u"V", u"Rhône-Alpes"), [
        (u"AI",  u"Ain"),
        (u"AH",  u"Ardèche"),
        (u"DM",  u"Drôme"),
        (u"HS",  u"Haute-Savoie"),
        (u"IS",  u"Isère"),
        (u"LR",  u"Loire"),
        (u"RH",  u"Rhône"),
        (u"SV",  u"Savoie"),
        ]),
]
