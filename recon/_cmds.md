

amass enum -src -ip -active -brute -d aboutyou.fr >> output/amass_aboutyou.fr  
amass intel -src -active -whois -ip -asn 44788,16509,48173,1137,13335,15169,14618,60955,6659,16378,8767 >> output/amass_asn_aboutyou.de
amass enum -src -ip -active -brute -d api-cloud.aboutyou.de >> output/amass_api-cloud.aboutyou.de
amass enum -src -ip -active -brute -d footlocker.id >> output/amass_footlocker.id
amass enum -src -ip -active -brute -addr 8.215.25.252 >> output/amass_footlocker_origin.id
amass intel -src -active -whois -ip -addr 8.215.25.252 >> output/amass_asn_aboutyou.de

