import json
import math
import os
import time

import requests
from dotenv import load_dotenv

load_dotenv()

LOCAL_CACHE_PATH = "shelters_cache.json"


class DrowsyShelterService:
    def __init__(self, cache_ttl=3600):
        self.api_key = os.getenv("DROWSY_SHELTER_API_KEY")
        self.base_url = "https://api.data.go.kr/openapi/tn_pubr_public_drowsy_shelter_api"
        self.cached_shelters = None
        self.cache_time = None
        self.cache_ttl = cache_ttl

        if not self.api_key:
            raise ValueError("DROWSY_SHELTER_API_KEY가 설정되지 않았습니다.")

        # 프로그램 시작 시 즉시 데이터 로드 시도
        self._load_shelters_on_start()

    def _load_shelters_on_start(self):
        """시작 시 API 호출 → 실패 시 로컬 캐시 파일 사용"""
        try:
            shelters = self.fetch_all_shelters()
            self.cached_shelters = shelters
            self.cache_time = time.time()
            self._save_local_cache(shelters)
            print(f"[DROWSY_SHELTER] 시작 시 데이터 로드 완료: {len(shelters)}개")
        except Exception as e:
            print(f"[DROWSY_SHELTER] API 호출 실패: {e}")
            shelters = self._load_local_cache()
            if shelters:
                self.cached_shelters = shelters
                self.cache_time = time.time()
                print(f"[DROWSY_SHELTER] 로컬 캐시 사용: {len(shelters)}개")
            else:
                print("[DROWSY_SHELTER] 로컬 캐시 없음 — 졸음쉼터 기능 비활성화")

    def _save_local_cache(self, shelters):
        try:
            with open(LOCAL_CACHE_PATH, "w", encoding="utf-8") as f:
                json.dump(shelters, f, ensure_ascii=False)
        except Exception as e:
            print(f"[DROWSY_SHELTER] 로컬 캐시 저장 실패: {e}")

    def _load_local_cache(self):
        try:
            with open(LOCAL_CACHE_PATH, "r", encoding="utf-8") as f:
                shelters = json.load(f)
                print(f"[DROWSY_SHELTER] 로컬 캐시 파일 로드: {LOCAL_CACHE_PATH}")
                return shelters
        except FileNotFoundError:
            return None
        except Exception as e:
            print(f"[DROWSY_SHELTER] 로컬 캐시 로드 실패: {e}")
            return None

    def find_nearest(self, current_lat, current_lng, limit=3):
        if not self.cached_shelters:
            return []

        try:
            current_lat = float(current_lat)
            current_lng = float(current_lng)
        except (TypeError, ValueError):
            print("[DROWSY_SHELTER] 현재 위치 좌표가 올바르지 않습니다.")
            return []

        results = []
        for shelter in self.cached_shelters:
            distance_km = calculate_distance_km(
                current_lat,
                current_lng,
                shelter["latitude"],
                shelter["longitude"],
            )
            results.append({**shelter, "distance_km": distance_km})

        results.sort(key=lambda s: s["distance_km"])
        return results[:limit]

    def get_shelters(self, force_refresh=False):
        if not force_refresh and self._is_cache_valid():
            return self.cached_shelters

        try:
            shelters = self.fetch_all_shelters()
            self.cached_shelters = shelters
            self.cache_time = time.time()
            self._save_local_cache(shelters)
            return shelters
        except Exception:
            if self.cached_shelters:
                print("[DROWSY_SHELTER] API 오류로 기존 캐시를 사용합니다.")
                return self.cached_shelters
            raise

    def fetch_all_shelters(self):
        num_of_rows = 1000
        first_page = self._request_page(page_no=1, num_of_rows=num_of_rows)
        total_count = self._get_total_count(first_page)
        shelters = self._parse_shelters(first_page)

        print(f"[DROWSY_SHELTER] totalCount={total_count}, loaded={len(shelters)}")

        if total_count <= num_of_rows:
            return shelters

        total_pages = math.ceil(total_count / num_of_rows)
        for page_no in range(2, total_pages + 1):
            page_data = self._request_page(page_no=page_no, num_of_rows=num_of_rows)
            shelters.extend(self._parse_shelters(page_data))

        print(f"[DROWSY_SHELTER] loaded_all={len(shelters)}")
        return shelters

    def _is_cache_valid(self):
        if self.cached_shelters is None or self.cache_time is None:
            return False
        return time.time() - self.cache_time < self.cache_ttl

    def _request_page(self, page_no, num_of_rows):
        url = (
            f"{self.base_url}"
            f"?serviceKey={self.api_key}"
            f"&pageNo={page_no}"
            f"&numOfRows={num_of_rows}"
            f"&type=json"
        )
        headers = {"User-Agent": "Mozilla/5.0"}
        last_error = None

        for attempt in range(3):
            try:
                response = requests.get(url, headers=headers, timeout=(5, 15))
                response.raise_for_status()
                return response.json()
            except requests.RequestException as e:
                last_error = e
                print(f"[DROWSY_SHELTER] 요청 재시도 {attempt + 1}/3 실패: {e}")
                time.sleep(1 + attempt)

        raise last_error

    def _get_total_count(self, data):
        body = data.get("response", {}).get("body", {})
        try:
            return int(body.get("totalCount", 0))
        except (TypeError, ValueError):
            return 0

    def _parse_shelters(self, data):
        body = data.get("response", {}).get("body", {})
        items = body.get("items", [])

        if isinstance(items, dict):
            items = items.get("item", [])
        if isinstance(items, dict):
            items = [items]
        if not isinstance(items, list):
            return []

        shelters = []
        skipped = 0

        for item in items:
            try:
                latitude = item.get("latitude")
                longitude = item.get("longitude")

                if not latitude or not longitude:
                    skipped += 1
                    continue

                shelters.append({
                    "name": item.get("shltrNm"),
                    "sido": item.get("ctprvnNm"),
                    "sigungu": item.get("signguNm"),
                    "road_name": item.get("roadRouteNm"),
                    "direction": item.get("roadRouteDrc"),
                    "address": item.get("rdnmadr") or item.get("lnmadr"),
                    "latitude": float(latitude),
                    "longitude": float(longitude),
                    "parking_count": item.get("prkplceCo"),
                    "toilet": item.get("toiletYn"),
                    "cctv_count": item.get("cctvCo"),
                    "phone": item.get("phoneNumber"),
                })
            except (AttributeError, TypeError, ValueError):
                skipped += 1

        if skipped:
            print(f"[DROWSY_SHELTER] skipped={skipped}")

        return shelters


def calculate_distance_km(lat1, lng1, lat2, lng2):
    earth_radius_km = 6371.0
    d_lat = math.radians(lat2 - lat1)
    d_lng = math.radians(lng2 - lng1)
    a = (
        math.sin(d_lat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(d_lng / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return earth_radius_km * c
