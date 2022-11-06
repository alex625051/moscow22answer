# moscow22answer
# Решение задачи 10 Лидеры инноваций Москвы

# API
GET http://37.230.196.15/arrangeKali/api/v1/postArrangeOrder/?targetArea=${targetArea}&targetDistrict=&targetDoorstep=${targetDoorstep}&targetCoverage=${targetCoverage}&targetPostsNumber=10

    targetArea: Адм округ
    targetDistrict: район (в формате район1,район2,оайон3 или пустой)
    targetDoorstep: доступность (в метрах)
    targetCoverage: охват населения всей Москвы (в %)
    targetPostsNumber: целевое количество постаматов
    В данной версии работает только район, целевое количество постоматов


#DEPLOY
 docker image build -t mapi22 .
 docker-compose up --build -d
