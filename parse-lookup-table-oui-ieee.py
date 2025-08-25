#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# скачивает CSV файлы с сайта ieee со списком MAC/vendor
# преобразует их в IPv6Network/vendor
# пишет файл в формате lookup-table для graylog

# при скачании с сайта ieee тот может отдавать 418 код и скрипт падает!
# в этом случае надо просто перезапустить скрипт, пока тот не отработает нормально

# если файлы с сайта уже есть в директории, то используются они
# для скачивания новых версии с сайта надо удалить ieee-*.csv файлы

import os
import csv
import re
import ipaddress
import urllib.request
import string

# csv файлы  IEEE
# Источник https://regauth.standards.ieee.org/standards-ra-web/pub/view.html#registries
in_urls = (
    ('https://standards-oui.ieee.org/oui/oui.csv',    'ieee-oui24.csv'), # /24
    ('https://standards-oui.ieee.org/oui28/mam.csv',  'ieee-oui28.csv'), # /28
    ('https://standards-oui.ieee.org/oui36/oui36.csv','ieee-oui36.csv'), # /36

    ('https://standards-oui.ieee.org/cid/cid.csv',    'ieee-cid24.csv'), # /24
    ('https://standards-oui.ieee.org/iab/iab.csv',    'ieee-iab36.csv'), # /36
)
# дополнительные адреса (broadcast/multicast и прочее) в формате как ieee
in_local_files = (
    ('', 'local-manual-oui.csv'),
)

dest_file   = '/etc/graylog/lookup-table/oui-ieee.csv'

tmp         = {}
tmp_vendors = {}

out         = []

def vendor_name_normalizer (in_vendor):
  # убираем пуктуацию и пробелы из имени вендора
  vendor_key = str(in_vendor).lower().translate(str.maketrans('', '', string.punctuation)).translate(str.maketrans('', '', string.whitespace))

  if vendor_key in tmp_vendors:
    vendor = tmp_vendors[vendor_key]
#    if in_vendor != vendor: print ("cu_vendor: {}\nin_vendor: {}".format(vendor, in_vendor))

  else:
    if (in_vendor[-1] == '.'):
      in_vendor = in_vendor[:-1].strip()  # удаляем точку в конце если есть
    vendor = in_vendor
    tmp_vendors[vendor_key] = vendor

  return (vendor)


def mac2ipv6 (_in_file):
  with open(_in_file, mode='rt') as csvfile:
    data = csv.reader(csvfile, dialect='unix')
    next(data, None) # пропускаем заголовок

    for row in data:
      mac    = row[1].strip()
      vendor = vendor_name_normalizer(row[2])

      mask   = (len(mac) * 4) # считаем маску для сети - каждый hex символ=4 bit

      mac    = mac.ljust(32,"0")                 # дополняем строку нулями до длины IPv6 - 32 символа
      mac    = ':'.join(re.findall('.{4}', mac)) # разделяем строку двоеточием каждые четыре символа - преобразуем в IPv6 формат
      mac    = ipaddress.IPv6Network('{}/{}'.format(mac, mask), strict=True).compressed # преобразуем в адрес IPv6 сети

#      if mac in tmp:
#        print ("Значение уже есть в списке: mac:{}, vendor: {} ".format(mac, tmp[mac]))
#        print ("Записано новое значение:    mac:{}, vendor: {} ".format(mac, vendor))
      tmp[mac] = vendor


for url, fn in in_urls:
  if not os.path.exists(fn):
    print ("Download url: {} to: {}".format(url, fn))
    urllib.request.urlretrieve(url, fn)

  print ("Parse file: {}".format(fn))
  mac2ipv6 (fn)
#  if os.path.exists(tmp_file): os.remove(tmp_file)

for url, fn in in_local_files:
  print ("Parse file: {}".format(fn))
  mac2ipv6 (fn)

tmp=dict(sorted(tmp.items()))
# подготовим словарь для передачи в csv
for mac, vendor in tmp.items():
  out.append({"mac": mac, "vendor": vendor})

print ("Write file to: {}".format(dest_file))

with open(dest_file, 'w', newline='') as fn:
  w = csv.DictWriter(f=fn, fieldnames=["mac", "vendor"], dialect=csv.unix_dialect, quoting=csv.QUOTE_ALL)
  w.writeheader()
  w.writerows(out)
