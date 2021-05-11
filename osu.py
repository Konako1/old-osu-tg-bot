import math
import operator
from functools import reduce
from aiogram.utils.markdown import quote_html

import pyttanko as pyttanko
from dataclasses import dataclass
from datetime import datetime
from pprint import pprint
from typing import Any, Iterator
from asyncio import sleep, create_task

import httpx
from dateutil import parser

import config

API_TOKEN = config.TG_TOKEN
BASE_URL = 'https://osu.ppy.sh/api/v2'
p = pyttanko.parser()


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
    completed: str
    miss: str
    bpm: int
    # position: int
    user_rank: int
    star_rating: float
    cover: str
    score_time: str
    map_url: str
    user_url: str
    flag: str
    pp: str


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
        score
):
    score_time = parser.parse(score['created_at'])
    score_time = score_time.replace(tzinfo=None)
    date_time_now = datetime.utcnow()
    time_has_passed = date_time_now - score_time
    time = str(time_has_passed).split(':')

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


async def get_pp_for_score(
        osu_file,
        score,
        print_status
) -> tuple[str, str, float]:
    expanded_beatmap_file = p.map(osu_file)
    mods_calc = reduce(operator.or_, (getattr(pyttanko, f'MODS_{mod}') for mod in score['mods'] if mod != 'PF' and mod != 'SD'),
                       pyttanko.MODS_NOMOD)
    stars = pyttanko.diff_calc().calc(expanded_beatmap_file, mods_calc)

    n100 = score['statistics']['count_100']
    n50 = score['statistics']['count_50']
    nmiss = score['statistics']['count_miss']
    objects = score['beatmap']

    objects_count = objects['count_circles'] + objects['count_sliders'] + objects['count_spinners']
    acc = round(score['accuracy']*100, 2)
    float_acc = acc
    fail_acc = pyttanko.acc_round(float_acc, objects_count, score['statistics']['count_miss'])

    pp_for_ss, *_ = pyttanko.ppv2(stars.aim, stars.speed, mods=mods_calc, bmap=expanded_beatmap_file)
    pp_if_fc, *_ = pyttanko.ppv2(stars.aim, stars.speed, mods=mods_calc, bmap=expanded_beatmap_file,
                                 n300=fail_acc[0] + nmiss, n100=fail_acc[1], n50=fail_acc[2], nmiss=0)
    pp_for_play, *_ = pyttanko.ppv2(stars.aim, stars.speed, mods=mods_calc, bmap=expanded_beatmap_file,
                                    n100=n100, n50=n50, nmiss=nmiss, combo=score['max_combo'])

    score_pp = score['pp']
    pp_correct = ''
    if score_pp is not None:
        pp_correct = f'{round(score_pp, 2)}pp'
    pp_only = f'{round(pp_for_play, 2)}pp'
    pp_ss = f'{round(pp_for_ss, 2)}pp if SS'
    pp_fc = f'{round(pp_if_fc, 2)}pp if FC'

    # print(pp_only)

    if score['rank'] == 'F':
        completed = 'Completed: {notpp}% of the map\n'.format(
            notpp=round((score['statistics']['count_100']
                         + score['statistics']['count_300']
                         + score['statistics']['count_50']
                         + score['statistics']['count_miss'])
                        /
                        (score['beatmap']['count_circles']
                         + score['beatmap']['count_sliders']
                         + score['beatmap']['count_spinners']) * 100, 2)
        )
        pp = f'{pp_fc} | {pp_ss}'
    else:
        completed = ''
        if print_status == 'Unranked':
            if score['perfect']:
                if score['accuracy'] == 1:
                    pp = pp_only
                else:
                    pp = f'{pp_only} | {pp_ss}'
            else:
                pp = f'{pp_only} | {pp_fc} | {pp_ss}'
        elif score_pp is None:
            if score['perfect']:
                if score['accuracy'] == 1:
                    pp = pp_only
                else:
                    pp = f'{pp_only} | {pp_ss}'
            else:
                pp = f'{pp_only} | {pp_fc} | {pp_ss}'
        else:
            if score['perfect']:
                if score['accuracy'] == 1:
                    pp = pp_correct
                else:
                    pp = f'{pp_correct} | {pp_ss}'
            else:
                pp = f'{pp_correct} | {pp_fc} | {pp_ss}'
    return completed, pp, stars.total


def print_pp_play(
        best_score,
        rank,
        accuracy,
        combo,
        score_time,
        url,
        get_more_info: bool,
        mods,
        starrate,
) -> str:
    play = f'<a href="{url}"><b>{quote_html(best_score["beatmapset"]["title"])}</b> by ' \
           f'<b>{quote_html(best_score["beatmapset"]["artist"])} ' \
           f'[{quote_html(best_score["beatmap"]["version"])}]</b></a>\n' \
           f'<b>{rank} {accuracy}{combo} {mods} {round(starrate, 2)}★</b>\n' \
           f'<b>{round(best_score["pp"], 2)}pp</b>\n'

    if get_more_info:
        play += f'{{{best_score["statistics"]["count_300"]} / {best_score["statistics"]["count_100"]}' \
                f' / {best_score["statistics"]["count_50"]} / ' \
                f'{best_score["statistics"]["count_miss"]}}}\n'

    play += f'{score_time}'
    return play


def get_map_status(
        score
):
    if score['beatmap']['status'] in ('graveyard', 'pending', 'wip'):
        return 'Unranked'
    return score['beatmap']['status'].capitalize()



# TODO: refactor this shit
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

    async def get_osu_file(
            self,
            map_id: int
    ) -> Iterator[str]:
        r = await self._session.get(f"https://osu.ppy.sh/osu/{map_id}")
        return r.iter_lines()

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

    async def get_user_nickname(self, user_id: int) -> tuple[str, str, str]:
        user_data = await self.get_user_data(user_id)
        url = f"https://osu.pp.sh/users/{user_data['id']}"
        return user_data['username'], user_data['rankHistory']['data'][-1], url

    # TODO: top5 recent notable scores
    # TODO: rank on a map method

    async def recent(
            self,
            user_id: int,
    ) -> Score:
        user_data = await self.get_user_data(user_id)

        user_rank = user_data['rankHistory']['data'][-1]
        r_score = await self.get_user_score(user_id, 'recent', 1)
        try:
            score = r_score[0]
        except IndexError:
            raise IndexError('User is quit w (no recent scores for past 24 hours)') from None

        result_time = get_deducted_time(score)

        beatmap = await self.get_beatmap(score['beatmap']['id'])

        print_status = get_map_status(score)

        misscount = ''
        if score['statistics']['count_miss'] != 0:
            misscount = f"{score['statistics']['count_miss']}xMiss"

        mods = ''.join(score['mods'])
        if mods == '':
            mods = 'NM'

        rank, accuracy = get_score_rank(score['rank'], score['accuracy'])

        if 'DT' in score['mods']:
            score['beatmap']['bpm'] *= 1.5

        if score['max_combo'] / beatmap['max_combo'] != 1:
            combo = f"{score['max_combo']}/{beatmap['max_combo']}x"
        else:
            combo = 'FC'

        url = f"https://osu.pp.sh/users/{user_data['id']}"

        flag = get_flag(user_data['country']['code'].lower())

        completed, pp, stars = await get_pp_for_score(await self.get_osu_file(beatmap['id']), score, print_status)

        # TODO: place on a leaderboard

        # score_on_beatmap = await self.get_user_beatmap_score(beatmap['id'], user_id)
        # pprint(user_data)
        # print(user_ranks)
        # pprint(r_score)
        # print(result_time)
        # pprint(beatmap)
        # pprint(score_on_beatmap)

        return Score(
            player=score['user']['username'],
            status=print_status,
            artist=score['beatmapset']['artist'],
            title=score['beatmapset']['title'],
            creator=score['beatmapset']['creator'],
            diff=score['beatmap']['version'],
            acc=accuracy,
            combo=combo,
            mods=mods,
            rank=rank,
            completed=completed,
            miss=misscount,
            bpm=score['beatmap']['bpm'],
            # position=score_on_beatmap['position'],   пока ненужная залупа
            user_rank=user_rank,
            star_rating=round(stars, 2),
            cover=score['beatmapset']['covers']['cover'],
            score_time=result_time,
            map_url=beatmap['url'],
            user_url=url,
            flag=flag,
            pp=pp
        )

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

        map_url = beatmap['url']

        print_status = get_map_status(best_score[0])

        _, _, starrate = await get_pp_for_score(await self.get_osu_file(beatmap['id']), best_score[0], print_status)

        mods = ''.join(best_score[0]['mods'])
        if mods == '':
            mods = 'NM'

        highest_pp_play = print_pp_play(best_score[0], rank, accuracy, combo, score_time, map_url, True, mods, starrate)

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
        # print(user_data['avatar_url'])

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
            play_time=round(user_data['statistics']['play_time'] / (60 * 60), 2),
            join_date=join_date,
            url=url,
        )
    # TODO: top5 user's best plays

    async def get_top5_best_plays(self, user_id: int) -> tuple[str, str]:
        try:
            best_score = await self.get_user_score(user_id, 'best', 5)
        except IndexError:
            raise IndexError("User hasn't set a single score yet")
        msg = ''
        map_pic_url = ''
        for i in range(5):
            beatmap = await self.get_beatmap(best_score[i]['beatmap']['id'])

            score_time = parser.parse(best_score[i]['created_at'])
            score_time = score_time.strftime('%d %B %Y')
            if score_time[i] == '0':
                score_time = score_time.lstrip('0')

            if best_score[i]['perfect']:
                combo = 'FC'
            else:
                combo = f'<b>{best_score[i]["max_combo"]}/{beatmap["max_combo"]}x</b>'

            rank, accuracy = get_score_rank(best_score[i]['rank'], best_score[i]['accuracy'])
            map_url = beatmap['url']

            if i == 0:
                map_pic_url = beatmap['beatmapset']['covers']['cover']

            mods = ''.join(best_score[i]['mods'])
            if mods == '':
                mods = 'NM'

            map_status = get_map_status(best_score[i])

            _, _, starrate = await get_pp_for_score(await self.get_osu_file(best_score[i]['beatmap']['id']), best_score[i], map_status)

            plays = print_pp_play(best_score[i], rank, accuracy, combo, score_time, map_url, False, mods, starrate)
            msg += f'{plays}\n\n'
        return msg, map_pic_url

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
            return 0
        user_id = response['id']
        return user_id

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
