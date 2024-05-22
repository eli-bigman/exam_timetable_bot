from bs4 import BeautifulSoup

# from bisect import bisect_left
import re
import logging
import aiohttp
import asyncio

from firebase_helper_functions import FirebaseHelperFunctions


logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


def id_search(id_ranges: list[str], id: int) -> bool:
    """
    Args:
        id_ranges(list[str]) - the lower and upper bound of the venue id ranges
        id(int) - the id to be found

    Returns:
        bool - whether the id falls within the range provided or not
    """

    lower, upper = map(int, id_ranges)
    return lower <= id <= upper


def get_single_exam_details(user_id: str, id: int, link: str, data: str) -> bool:
    """
    Get the all exams details of a single course.

    This funtion takes the links of all exams
    schedule returned from the results of a search
    in the "search schedule tab" in sts.timetable
    website and saves the exams details to firebase
    """
    try:
        found_exact_venue = False
        firebase = FirebaseHelperFunctions(user_id)
        soup = BeautifulSoup(data, "lxml")
        course_name = soup.select("div.header span.text-primary")[0].text
        table = soup.find("table", class_="table table-striped")

        if not table:
            return False

        course_level = (
            table.find("td", string="Course Level").find_next_sibling("td").text
        )

        exams_status = (
            table.find("td", string="Exams Status").find_next_sibling("td").text
        )

        exam_date = table.find("td", string="Exam Date").find_next_sibling("td").text

        exam_time = table.find("td", string="Exams Time").find_next_sibling("td").text

        campus = table.find("td", string="Campus").find_next_sibling("td").text

        venues = (
            table.find("td", string="Venue(s) / Index Range")
            .find_next_sibling("td")
            .find_all("li")
        )

        for venue in venues:
            venue_text = venue.text.strip().split("|")
            id_range = venue_text[1]
            venue_name = venue_text[0]
            all_venues = [
                venue.text.strip("[]").replace("[", "") for venue in venues
            ]

            no_id_venue = []
            if id_range == "":
                no_id_venue.append(venue_name)
                continue

            venue_id_range = re.findall(r"\d+", id_range)

            if not len(venue_id_range) == 2:
                logger.info(f"Venue Not Found ❌: {venue_name}")
                continue


            if id_search(venue_id_range, id):
                exact_venues_details = {
                    "Full_Course_Name": course_name,
                    "Course_Level": course_level,
                    "Campus": campus,
                    "Exams_Status": exams_status,
                    "Exams_Date": exam_date,
                    "Exams_Time": exam_time,
                    "Exact_Venue": f"{venue_name} | {id_range}",
                    "No_ID_Venue": no_id_venue,
                    "Link": link,
                }
                found_exact_venue = True
                firebase.save_exact_venue_details(
                    course_name, exact_venues_details
                )
                # logger.info(f"Venue Found ✅: {venue_name} | {id_range}")
            else:
                venue_not_found_details = {
                    "Full_Course_Name": course_name,
                    "Course_Level": course_level,
                    "Campus": campus,
                    "Exams_Status": exams_status,
                    "Exams_Date": exam_date,
                    "Exams_Time": exam_time,
                    "Exact_Venue": None,
                    "All_Exams_Venues": all_venues,
                    "Link": link,
                }
                firebase.save_exact_venue_not_found_details(
                    course_name, venue_not_found_details
                )
                # logger.info(f"Venue Not Found ❌: {venue_name}")
        return found_exact_venue

    except Exception as e:
        logger.error(f"ERROR GETTING SINGLE_EXAMS_DETAIL: {str(e)}")
        return


async def fetch_url(url: str) -> str:
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as request:
            return await request.text()


async def main(user_id: str, student_id: int, links: list) -> bool:
    try:
        found_exact_venue = False
        FirebaseHelperFunctions(user_id).delete_exams_details()

        tasks = [fetch_url(link) for link in links]
        res = await asyncio.gather(*tasks)

        if not res:
            raise Exception("No links found")
            


        for idx in range(len(res)):
            result = get_single_exam_details(
                user_id, id=student_id, link=links[idx], data=res[idx]
            )
            if result:
                found_exact_venue = True

        return found_exact_venue

    except Exception as e:
        logger.error(f"Error proccesing exams details: {str(e)}")
        return


if __name__ == "__main__":
    exams_links = [
        "https://sts.ug.edu.gh/timetable/details/UGRC150/2024-04-03",
        "https://sts.ug.edu.gh/timetable/details/UGRC150-Main Campus-Batch 1/2024-04-03",
        "https://sts.ug.edu.gh/timetable/details/UGRC150-Main Campus-Batch 2/2024-04-03",
        "https://sts.ug.edu.gh/timetable/details/UGRC150-Main Campus-Batch 3/2024-04-03",
        "https://sts.ug.edu.gh/timetable/details/UGRC150-Main Campus-Batch 4/2024-04-03",
        "https://sts.ug.edu.gh/timetable/details/UGRC150-Main Campus-Batch 5/2024-04-03",
        "https://sts.ug.edu.gh/timetable/details/UGRC150-Main Campus-Batch 6/2024-04-03",
        "https://sts.ug.edu.gh/timetable/details/UGRC150-Main Campus-Batch 7/2024-04-03",
        "https://sts.ug.edu.gh/timetable/details/UGRC150-CHS-Batch - 1/2024-04-04",
        "https://sts.ug.edu.gh/timetable/details/UGRC150-CHS-Batch - 2/2024-04-04",
    ]

    # user_id = "123456789"
    ID = 22048836

    # UID = "271330483"
    UID = "123456789"
    asyncio.run(main(UID, ID, exams_links))