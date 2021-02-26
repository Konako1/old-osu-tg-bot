import math
from dataclasses import dataclass
from datetime import datetime
from pprint import pprint
from typing import Any
from asyncio import sleep, create_task

import httpx
from dateutil import parser

import config

API_TOKEN = config.TG_TOKEN
BASE_URL = 'https://osu.ppy.sh/api/v2'


def api_build_url(fragment: str) -> str:
    return BASE_URL + '/' + fragment.lstrip('/')


@dataclass()
class UserInfo:
    avatar: str
    flag: str
    user: str
    pp: int
    global_rank: int
    country_rank: int
    rank_change: str
    playcount: int
    highest_pp_play: str
    fp_count: int
    lvl_current: int
    lvl_progress: int
    profile_acc: float
    replays_watched: int
    discord: str
    play_count: int
    play_time: float
    join_date: str
    url: str


@dataclass()
class Score:
    player: str
    status: str
    artist: str
    title: str
    creator: str
    diff: str
    acc: str
    combo: str
    mods: str
    rank: str
    comp_or_pp: str
    miss: str
    bpm: int
    # position: int
    user_ranks: int
    star_rating: float
    cover: str
    score_time: str
    map_url: str
    user_url: str
    flag: str


# async def main():
#     token = await request_to_osu()
#     nick = input('Введите ник: ')
#     await recent(nick, token)
#     await session.aclose()


def get_flag(
        code: str
) -> str:
    flag = ''
    for letter in code:
        flag += f':regional_indicator_{letter.lower()}:'
    return flag


def get_score_rank(
        rank: str,
        acc: float
) -> tuple[str, str]:
    accuracy = f'{round(acc * 100, 2)}% '
    ranks = {
        'XH': "SS+",
        'X': "SS",
        'SH': 'S+'
    }
    if accuracy == '100.00% ':
        accuracy = ''
    return ranks.get(rank, rank), accuracy


def get_deducted_time(
        time: list[str]
):
    if time[0] == '0':
        if time[1][0] == '0':
            time[1] = time[1][1]
        if time[1] != '01':
            if time[1] == '0':
                time = 'less then a minute ago'
            else:
                time = f'{time[1]} minutes ago'
        else:
            time = 'about a minute ago'
    else:
        if time[0] != '1':
            if time[1] < '30':
                time = f'about {time[0]} hours ago'
            else:
                rt = int(time[0]) + 1
                time = f'about {rt} hours ago'
        else:
            time = f'about an hour ago'
    return time


class Osu:
    def __init__(self, token: str):
        self._token = token
        self._session = httpx.AsyncClient()

    async def update_token(self, delay: int = 0) -> None:
        if delay:
            await sleep(delay)
        resp = await self._session.post('https://osu.ppy.sh/oauth/token', json={
            'client_id': config.id,
            'client_secret': config.secret,
            'grant_type': 'client_credentials',
            'scope': 'public',
        })
        resp.raise_for_status()
        data = resp.json()
        self._token = data['access_token']
        create_task(self.update_token(data['expires_in'] - 60))

    # TODO: updating token
    async def api_request(
            self,
            http_method: str,
            method: str,
            params: dict[str, Any],
    ) -> dict:
        url = api_build_url(method)
        if http_method == 'GET':
            response = await self._session.get(
                url,
                headers={'Authorization': 'Bearer ' + self._token},
                params=params
            )
        else:
            raise NotImplementedError
        response.raise_for_status()
        return response.json()

    async def get_user_beatmap_score(
            self,
            beatmap_id: int,
            user_id: int,
    ) -> dict:
        return await self.api_request(
            'GET',
            '/beatmaps/{beatmap}/scores/users/{user}'.format(beatmap=beatmap_id, user=user_id),
            {}
        )

    async def get_user_score(
            self,
            user_id: int,
            score_type: str,
            limit: int,
    ) -> dict:
        return await self.api_request(
            'GET',
            '/users/{user}/scores/{type}'.format(user=user_id, type=score_type),
            {'limit': limit, 'include_fails': 1}
        )

    # async def search_by_nick(
    #         self,
    #         query: str,
    # ) -> int:
    #     is_in_cache = await database.get_cached_user(query)
    #     if is_in_cache is not None:
    #         return is_in_cache
    #     is_in_api = await self.api_request(
    #         'GET',
    #         '/search',
    #         {'query': query, 'mode': 'user', 'page': 0}
    #     )
    #
    #     try:
    #         response = is_in_api['user']['data'][0]
    #     except IndexError:
    #         raise IndexError('User not found') from None
    #     user_id = response['id']
    #     await database.cache_user(query, user_id)
    #     return user_id

    async def get_beatmap(
            self,
            beatmap_id: int,
    ) -> dict:
        return await self.api_request(
            'GET',
            '/beatmaps/{beatmap}'.format(beatmap=beatmap_id),
            {}
        )

    async def get_user_data(
            self,
            user_id: int,
    ) -> dict:
        return await self.api_request(
            'GET',
            '/users/{user}'.format(user=user_id),
            {}
        )

    # TODO: top5 recent notable scores

    async def recent(
            self,
            user_id: int,
    ) -> Score:
        user_data = await self.get_user_data(user_id)
        user_ranks = user_data['rankHistory']['data'][-1]
        r_score = await self.get_user_score(user_id, 'recent', 1)
        try:
            score = r_score[0]
        except IndexError:
            raise IndexError('User is quit w (no recent scores for past 24 hours)') from None

        score_time = parser.parse(score['created_at'])
        score_time = score_time.replace(tzinfo=None)
        date_time_now = datetime.utcnow()
        time_has_passed = date_time_now - score_time
        result_time = get_deducted_time(str(time_has_passed).split(':'))

        beatmapset = score['beatmapset']
        beatmap_stat = score['beatmap']
        status = beatmap_stat['status']
        user = score['user']
        stat = score['statistics']
        cover = beatmapset['covers']['cover']

        beatmap = await self.get_beatmap(beatmap_stat['id'])

        # score_on_beatmap = await self.get_user_beatmap_score(beatmap_stat['id'], user_id)

        if status in ('graveyard', 'pending', 'wip'):
            print_status = 'Unranked'
        else:
            print_status = status.capitalize()

        misscount = ''
        if stat['count_miss'] != 0:
            misscount = '{miss}xMiss'.format(miss=stat['count_miss'])

        mods = ''.join(score['mods'])
        if mods == '':
            mods = 'NM'

        rank, accuracy = get_score_rank(score['rank'], score['accuracy'])

        if score['rank'] == 'F':
            completed = 'Completed: {notpp}% of the map'.format(
                notpp=round((stat['count_100']
                             + stat['count_300']
                             + stat['count_50']
                             + stat['count_miss'])
                            /
                            (beatmap_stat['count_circles']
                             + beatmap_stat['count_sliders']
                             + beatmap_stat['count_spinners']) * 100, 2)
            )
        else:
            pp = score['pp']
            if print_status == 'Unranked':
                completed = 'PP: 0'
            elif pp is None:
                completed = 'Player have a better score'
            else:
                completed = 'PP: {pp}'.format(pp=round(pp, 2))

        # TODO: pp if FC / pp if SS (невозможная залупа)
        if 'DT' in score['mods']:
            beatmap_stat['bpm'] *= 1.5

        if score['max_combo'] / beatmap['max_combo'] != 1:
            combo = f"{score['max_combo']}/{beatmap['max_combo']}x"
        else:
            combo = 'FC'

        url = f"https://osu.pp.sh/users/{user_data['id']}"

        flag = get_flag(user_data['country']['code'].lower())

        # TODO: mods star rate (еще одна залупа)

        # pprint(user_data)
        # print(user_ranks)
        # pprint(r_score)
        # print(result_time)
        # pprint(beatmap)
        # pprint(score_on_beatmap)

        return Score(
            player=user['username'],
            status=print_status,
            artist=beatmapset['artist'],
            title=beatmapset['title'],
            creator=beatmapset['creator'],
            diff=beatmap_stat['version'],
            acc=accuracy,
            combo=combo,
            mods=mods,
            rank=rank,
            comp_or_pp=completed,
            miss=misscount,
            bpm=beatmap_stat['bpm'],
            # position=score_on_beatmap['position'],   пока ненужная залупа
            user_ranks=user_ranks,
            star_rating=beatmap_stat['difficulty_rating'],
            cover=cover,
            score_time=result_time,
            map_url=beatmap['url'],
            user_url=url,
            flag=flag
        )

    # TODO: top5 user's best plays

    async def user_info(
            self,
            user_id: int,
            # mode: Optional[str],
    ) -> UserInfo:
        user_data = await self.get_user_data(user_id)
        # pprint(user_data)

        # print(len(user_data['rank_history']['data']))
        # print(user_data['rank_history']['data'][-1])
        # print(user_data['rank_history']['data'][-7])

        try:
            best_score = await self.get_user_score(user_id, 'best', 1)
        except IndexError:
            raise IndexError("User hasn't set a single score yet")
        # pprint(best_score)

        beatmap = await self.get_beatmap(best_score[0]['beatmap']['id'])
        # pprint(beatmap)

        score_time = parser.parse(best_score[0]['created_at'])
        score_time = score_time.strftime('%d %B %Y %H:%M:%S')
        if score_time[0] == '0':
            score_time = score_time.lstrip('0')

        if best_score[0]['perfect']:
            combo = 'FC'
        else:
            combo = f'<b>{best_score[0]["max_combo"]}/{beatmap["max_combo"]}x</b>'

        rank, accuracy = get_score_rank(best_score[0]['rank'], best_score[0]['accuracy'])

        highest_pp_play = f'<b>{best_score[0]["beatmapset"]["title"]}</b> by ' \
                          f'<b>{best_score[0]["beatmapset"]["artist"]} ' \
                          f'[{best_score[0]["beatmap"]["version"]}]</b>\n' \
                          f'<b>{rank} {accuracy}{combo}</b>\n' \
                          f'{{{best_score[0]["statistics"]["count_300"]} / {best_score[0]["statistics"]["count_100"]}' \
                          f' / {best_score[0]["statistics"]["count_50"]} / ' \
                          f'{best_score[0]["statistics"]["count_miss"]}}}\n' \
                          f'<b>{best_score[0]["pp"]}pp</b>\n' \
                          f'{score_time}'

        rank_change = user_data['rank_history']['data'][-7] - user_data['rank_history']['data'][-1]
        if rank_change > 0:
            rank_change = f'gained {int(math.fabs(rank_change))} ranks'
        else:
            rank_change = f'lost {int(math.fabs(rank_change))} ranks'

        join_date = parser.parse(user_data['join_date'])
        join_date = join_date.strftime("%d %B %Y")
        if join_date[0] == '0':
            join_date = join_date.lstrip('0')

        if user_data["discord"] is None:
            discord = ''
        else:
            discord = f"Discord: {user_data['discord']}\n"

        if user_data['avatar_url'].startswith('/'):
            user_data['avatar_url'] = f"https://osu.ppy.sh{user_data['avatar_url']}"
        print(user_data['avatar_url'])

        url = f"https://osu.ppy.sh/users/{user_data['id']}"

        flag = get_flag(user_data['country']['code'].lower())

        return UserInfo(
            avatar=user_data['avatar_url'],
            flag=flag,
            user=user_data['username'],
            pp=round(user_data['statistics']['pp']),
            global_rank=user_data['statistics']['global_rank'],
            country_rank=user_data['statistics']['country_rank'],
            rank_change=rank_change,
            playcount=user_data['statistics']['play_count'],
            highest_pp_play=highest_pp_play,
            fp_count=user_data['scores_first_count'],
            lvl_current=user_data['statistics']['level']['current'],
            lvl_progress=user_data['statistics']['level']['progress'],
            profile_acc=round(user_data['statistics']['hit_accuracy'], 2),
            replays_watched=user_data['statistics']['replays_watched_by_others'],
            discord=discord,
            play_count=user_data['statistics']['play_count'],
            play_time=round(user_data['statistics']['play_time'] / (60*60), 2),
            join_date=join_date,
            url=url,
        )

    async def get_user_id(
            self,
            query: str
    ) -> int:
        is_in_api = await self.api_request(
            'GET',
            '/search',
            {'query': query, 'mode': 'user', 'page': 0}
        )

        try:
            response = is_in_api['user']['data'][0]
        except IndexError:
            raise IndexError('User not found') from None
        user_id = response['id']
        return user_id

    # TODO: make a database

    # TODO: download song from beatmap (сложная пизда)

    # TODO: best user's score on map

    async def close(self):
        await self._session.aclose()


async def request_to_osu() -> Osu:
    osu = Osu('')
    await osu.update_token()
    return osu


# if __name__ == '__main__':
#     run(main())
