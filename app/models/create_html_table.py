import pandas as pd
class Table:
    def __init__(self, table=None, columns=['Вопрос', 'Ответ', 'Вероятность']):
        if table is None:
            self._table = pd.DataFrame(columns=columns)
        else:
            self._table = table
        self._index_available = 0
        self._columns = columns
        self._html_template = '''<html>
        <head>
            <meta charset="utf-8">
            <link rel="stylesheet" type="text/css" href="../static/style_table.css"/>
	    </head>
        <body>
            {table}
            <script src="../static/doubleClickRowTable.js"></script>
        </body>
        </html>
        '''
            
    def add_row(self, row):
        self._table.loc[self._index_available] = row
        self._index_available += 1
    
    def save_html(self, path="table.html", table_id="table_prob"):
        with open(path, 'w', encoding="utf-8") as f:
            f.write(
                self._html_template.format(
                    table=self._table.to_html(
                        classes='mystyle', 
                        table_id=table_id,
                        justify="left",
                    )
                )
            )
    
    def clear_table(self, ):
        del(self._table)
        self._table = pd.DataFrame(columns=self._columns)
        self._index_available = 0

if __name__ == "__main__":
    table = Table()
    table.add_row('Вопрос', 'Ответ', 0.7)
    table.add_row('Ответ', 'Вопрос', 0.7)
    table.add_row('Вопрос', 'Ответ', 0.7)
    table.add_row('Ответ', 'Вопрос', 0.7)
    table.add_row('Вопрос', 'Ответ', 0.7)
    table.add_row('Ответ', 'Вопрос', 0.7)
    table.add_row('Вопрос', 'Ответ', 0.7)
    table.add_row('Ответ', 'Вопрос', 0.7)
    table.add_row('Вопрос', 'Ответ', 0.7)
    table.add_row('Ответ', 'Вопрос', 0.7)
    table.add_row('Вопрос', 'Ответ', 0.7)
    table.add_row('Ответ', 'Вопрос', 0.7)
    table.add_row('Вопрос', 'Ответ', 0.7)
    table.add_row('Ответ', 'Вопрос', 0.7)
    table.save_html()