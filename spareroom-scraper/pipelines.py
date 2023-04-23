import re
from typing import Any
import scrapy
from itemadapter import ItemAdapter
from scrapy.exceptions import DropItem


class SpareRoomPipeline:
    '''
    Can implement a pipeline here for dropping duplicates, dropping
    data with issues or that isn't relevant (e.g. already been let/unavailable)
    Alternatively can just do this downstream in Spark.
    '''
    def clean_list(
            self,
            data: list[str]
    ) -> list[str]:
        """
        Strip out spaces and newlines 
        and remove resulting empty strings 
        from list
        """
        data = list(map(lambda x: re.sub(r'[\n\t]*', '', x).strip(), data))
        data = [re.sub(r'\s+', ' ', entry) for entry in data]
        data = [entry for entry in data if entry != '']
        return data

    def item_list_to_dict(
            self,
            item: Any,
            key: str,
            columns: list[str]
            ) -> ItemAdapter:
        """
        Convert a list of keys and values
        from a spareroom Item to a dictionary
        Example:
        ['Available', 'Now', 'Minimum term', '3 months', 'Maximum term', '6 months']
        to
        {'Available': 'Now', 
        'Minimum term': '3 months',
        'Maximum term': '6 months'}
        """
        adapter = ItemAdapter(item)
        if adapter.get(key):
            result = {}
            for col in columns:
                try:
                    result[col] = item[key][item[key].index(col)+1]
                except (ValueError, IndexError):
                    result[col] = None
            item[key] = result 
        else:
            item[key] = dict.fromkeys(columns, None)
        return item

    def get_room_price(
            self,
            item: Any
            ) -> Any:
        """
        Get the price and deposit for rooms in a listing.
        Note: When a room has been LET the deposit for that room 
        dissapears from the listing. Deposits have a (Room i) key to 
        identify the index of the room that they refer to so we use this
        to match deposits with rooms. 
        """
        adapter = ItemAdapter(item)
        room_price = []
        if adapter.get('room_price'):
            room_price = [{'price': item['room_price'][i],
                           'type': item['room_price'][i+1], 
                           'deposit': None, 
                           'bills_included': None} \
                        for i in range(len(item['room_price'])) if i % 2 == 0]
        else:
            item['room_price'] = room_price
            return item
        room_list = [entry for entry in item['room_deposit'] if '(Room ' in entry]
        if room_list:
            for entry in room_list:
                index = int(re.findall(r'\d+', entry)[0])
                room_price[index-1]['deposit'] = item['room_deposit'][
                                            item['room_deposit'].index(entry)+1
                                            ]
                room_price[index-1]['bills_included'] = item['room_deposit'][
                                            item['room_deposit'].index('Bills included?')+1
                                            ]
        else:
            for entry in room_price:
                if entry['type'] != '(NOW LET)':
                    try:
                        entry['deposit'] = item['room_deposit'][
                                                item['room_deposit'].index('Deposit')+1
                                                ]
                    except (IndexError, ValueError):
                        entry['deposit'] = None
                try:
                    entry['bills_included'] = item['room_deposit'][
                                                item['room_deposit'].index('Bills included?')+1
                                                ]
                except (IndexError, ValueError):
                    entry['bills_included'] = None
        item['room_price'] = room_price
        return item

    def process_item(
            self,
            item: Any,
            spider: scrapy.Spider
            ) -> Any:
        """
        Process an Item scraped by the spider to tidy it up
        into convenient JSON structure for downstream use-cases
        """
        adapter = ItemAdapter(item)
        # all text cleans
        for key in list(adapter.asdict().keys()):
            item[key] = self.clean_list(item[key])
            # item[key] = list(map(lambda x: re.sub(r'[\n\t]*', '', x).strip(), item[key]))
            # item[key] = [re.sub(r'\s+', ' ', entry) for entry in item[key]]
            # item[key] = [entry for entry in item[key] if entry != '']

        if adapter.get('ad_ref'):
            item['ad_ref'] = [ref for ref in item['ad_ref'] if ref.startswith('Ad ref#')][0]
        else:
            raise DropItem('Missing ad ref in item')         
        listing_type = {'list_type': item['listing_type'][0],
                        'location': item['listing_type'][1],
                        'postcode': item['listing_type'][2]}
        item['listing_type'] = listing_type

        # property price
        if adapter.get('property_price'):
            property_price = {'price': item['property_price'][0], 
                            'description': ' '.join(item['property_price'][1:]),
                            'deposit': item['room_deposit'][
                                            item['room_deposit'].index('Security deposit')+1
                                            ]
                                            }
        else:
            property_price = {'price': None, 'description': None, 'deposit': None}
        item['property_price'] = property_price

        # amenities
        amenities_cols = ['Furnishings', 'Parking',
                          'Garage', 'Garden/terrace', 
                          'Balcony/patio', 'Disabled access', 
                          'Living room', 'Broadband included']
        item = self.item_list_to_dict(item, 'amenities', amenities_cols)

        # household preferences
        household_pref_cols = ['Couples OK?', 'Smoking OK?',
                               'Pets OK?', 'Occupation', 
                               'References?', 'Min age', 
                               'Max age', 'Gender']
        item = self.item_list_to_dict(item, 'household_preferences', household_pref_cols)
        # current household
        current_house_cols = ['# housemates', '# flatmates',
                              'Total # rooms', 'Age', 
                              'Ages', 'Smoker?', 
                              'Any pets?', 'Language', 
                              'Nationality', 'Gender', 
                              'Interests', 'Occupation', 
                              'Orientation']
        item = self.item_list_to_dict(item, 'current_household', current_house_cols)

        # room available
        room_available_cols = ['Available', 'Minimum term', 'Maximum term']
        item = self.item_list_to_dict(item, 'room_available', room_available_cols)

        item = self.get_room_price(item)
        item.pop('room_deposit')

        return item
    