

amass enum -src -ip -active -brute -d aboutyou.fr >> output/amass_aboutyou.fr  
amass intel -src -active -whois -ip -asn 44788,16509,48173,1137,13335,15169,14618,60955,6659,16378,8767 >> output/amass_asn_aboutyou.de
amass enum -src -ip -active -brute -d api-cloud.aboutyou.de >> output/amass_api-cloud.aboutyou.de