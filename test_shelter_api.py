from src.rest_area_service import DrowsyShelterService

TEST_LAT = 37.4979
TEST_LNG = 127.0276

def main():
    service = DrowsyShelterService()
    results = service.find_nearest(TEST_LAT, TEST_LNG, limit=3)

    if not results:
        print("결과 없음")
        return

    for i, s in enumerate(results, 1):
        print(f"{i}. {s['name']}  {s['distance_km']:.2f}km")
        print(f"   {s['road_name']} {s['direction']}")
        print(f"   {s['address']}")

if __name__ == "__main__":
    main()