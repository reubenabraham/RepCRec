from constants import UP, DOWN, site_variables_init


class DataItem:
    '''
    Contains data item info like:
    - name
    - comitted value, temp value
    - replicated or not
    '''
    def __init__(self, name: str, value: str):
        self.name = name
        self.committed_value = value
        self.temp_value = None
        self.replicated = False

    def __repr__(self):
        return self.name+"="+self.committed_value


class LockManager:
    def __init__(self, variable: str):
        self.data_item_name = variable
        self.lock = None

    def clear_locks(self):
        self.lock = None


class SiteDataManager:
    '''
    Each site gets its own SiteDataManager.
    SDM stores:
    -the data of the site
    -the lock table for the site - each variable on the site has its own LockManager
    -status of the site
    '''

    def __init__(self, site_id: str):

        self.status = UP
        self.site_number = site_id
        self.data_dict = dict()
        self.lock_table = dict()
        self.initialise_site()

    def __repr__(self):
        return self.site_dump()

    def initialise_site(self):
        '''
        Set initial variable values for this site
        '''

        for var in site_variables_init[self.site_number]:
            data_item_name = "x"+str(var)
            obj = DataItem(data_item_name, str(var*10))
            if var % 2 == 0:
                obj.replicated = True

            self.data_dict[data_item_name] = obj

    def site_dump(self):
        output_string = "Site "
        output_string += self.site_number
        output_string += ": "+f"Status:[{'UP' if self.status else 'DOWN'}]"+" - "
        for data_item in self.data_dict.values():
            output_string += data_item.name+":"+data_item.committed_value+", "

        return output_string[:-2]



