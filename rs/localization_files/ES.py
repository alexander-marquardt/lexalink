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

# Spain
ES_regions = [
    (( u'AN', u'Andalucía'),
     [(u'AL', u'Almería'), 
      (u'CA', u'Cádiz'), 
      (u'CO', u'Córdoba'), 
      (u'GR', u'Granada'), 
      (u'H',  u'Huelva'), 
      (u'J',  u'Jaén'), 
      (u'MA', u'Málaga'), 
      (u'SE', u'Sevilla')]),
    
    ((u'AR', u'Aragón'),
    [(u'HU', u'Huesca'), 
     (u'TE', u'Teruel'), 
     (u'Z',  u'Zaragoza')]),
    
    ((u'O', u'Asturias'), 
    [(u'O', u'Asturias')]),
    
    ((u'IB', u'Beleares'),
     # the following region codes are invented (for islands)-- these are not official
     # regions. But doesn't matter for purposes of indexing into the database.
    [(u'MA', u'Mallorca'), 
     (u'ME', u'Menorca'), 
     (u'IB', u'Ibiza'), 
     (u'FO', u'Formentera')]),
    
    ((u'CN', u'Canarias'),
    [(u'GC', u'Las Palmas'), 
     (u'TF', u'Santa Cruz de Tenerife')]),
    
    ((u'S', u'Cantabria'),
    [(u'S', u'Cantabria')]),
    
    ((u'CL', u'Castilla y León'), 
    [(u'AV', u'Avila'), 
     (u'BU', u'Burgos'), 
     (u'LE', u'León'), 
     (u'P',  u'Palencia'),
     (u'SA', u'Salamanca'),
     (u'SG', u'Segovia'), 
     (u'SO', u'Soria'), 
     (u'VA', u'Valladolid'),
     (u'ZA', u'Zamora')]),
    
    ((u'CM', u'Castilla la Mancha'),
    [(u'AB', u'Albacete'),
     (u'CR', u'Ciudad Real'),
     (u'LE', u'León'),
     (u'CU', u'Cuenca'),
     (u'GU', u'Guadalajara'),
     (u'TO', u'Toledo')]),
    
    ((u'CT', u'Cataluña'), 
    [(u'B',  u'Barcelona'),
     (u'GI', u'Girona'),
     (u'L',  u'Lleida'),
     (u'T',  u'Tarragona')]),
    
    ((u'CE', u'Ceuta'),
    [(u'CE', u'Ceuta')]),
    
    ((u'EX', u'Extremadura'), 
    [(u'BA', u'Badajoz'),
     (u'CC', u'Cáceres')]),
    
    ((u'GA', u'Galicia'),
    [(u'C',  u'A Coruña'),
     (u'LU', u'Lugo'),
     (u'OR', u'Orense'),
     (u'PO', u'Pontevedra')]),
    
    ((u'LO', u'La Rioja'), 
    [(u'LO', u'La Rioja')]),
    
    ((u'M',  u'Madrid'),
    [(u'M', u'Área Metropolitana'),
     (u'1', u'Comarca de Las Vegas'),
     (u'2', u'Comarca Sur'),
     (u'3', u'Cuenca Alta del Manzanares'),
     (u'4', u'Cuenca del Guadarrama'),
     (u'5', u'Cuenca del Henares'),
     (u'6', u'Cuenca del Medio Jarama'),
     (u'7', u'Sierra Norte'),
     (u'8', u'Sierra Oeste'),
     ]),
    
    ((u'ML', u'Melilla'), 
    [(u'ML', u'Melilla')]),
    
    ((u'MU', u'Murcia'), 
    [(u'MU', u'Murcia')]),
    
    ((u'NA', u'Navarra'), 
    [(u'NA', u'Navarra')]),  
    
    ((u'PV', u'País Vasco'),
    [(u'VI', u'Álava'),
     (u'SS', u'Giupúzcoa'),
     (u'BI', u'Vizcaya')]),
    
    ((u'CV', u'Valencia'), 
    [(u'A',  u'Alicante'),
     (u'CS', u'Castellón'),
     (u'V',  u'Valencia')])                         
    ]