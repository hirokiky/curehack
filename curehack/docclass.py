# -*- coding: utf-8 -*-

"""
=========
LICENSE
=========

『集合知プログラミング』 Toby Segaran著 978-0-596-52932-1
に掲載されたソースコードを元に改変を加えています。

同書「はじめに」より引用します。本資料に含まれるプログラムを利用する
場合も同様の規定に従ってください。

> 本書はあなたが仕事を解決する手助けになるために存在している。本書内のコー
> ドはあなたのプログラムやドキュメントの中で利用してもよい。コードの大部
> 分を複製するのでなければ、許可を取るためにわれわれにコンタクトを取る必
> 要はない。たとえば、本書からのコードのいくつかを利用するようなプログラ
> ムを書く場合であれば、許可を求める必要はない。オライリーの本からの例題
> の CD-ROM を販売したり、配布するような場合には許可が必要である。本書の
> 例題のコードを引用して質問に回答するような場合には許可を求める必要はな
> い。本書からのコード例を大量にあなたの製品のドキュメントに含める場合に
> は許可を得る必要がある。出典の表示をしていただければ、我々は感謝する
> が、これは必須ではない。通常出典の表示はタイトル、著者、出版社、ISBNを
> 含む。たとえば「『集合知プログラミング』Toby Segaran著、
> 978-0-596-52932-1」のような形である。

And thanks to @knzm for improving the sample code!
https://bitbucket.org/knzm/collective/
"""

import re
import math


DefaultClassifier = lambda backend: NaiveBayesClassifier(get_words,
                                                         backend)


def get_words(doc):
    splitter = re.compile(r'\W*')
    words = [s.lower() for s in splitter.split(doc)
             if 2 < len(s) < 20]
    return dict([(w, 1) for w in words])


class MongoDBBackend(object):
    def __init__(self, db, user):
        self.db = db
        self.user = user

    def inc_feature(self, feature, cat):
        """特徴 feature がカテゴリ cat に出現した回数を 1 増やす"""
        features = self.db.features.find({'user': self.user,
                                          'feature': feature,
                                          'category': cat})
        if features.count():
            self.db.features.update({'user': self.user,
                                     'feature': feature,
                                     'category': cat},
                                    {'$inc': {'count': 1.0}})
        else:
            self.db.features.insert({'user': self.user,
                                     'feature': feature,
                                     'category': cat,
                                     'count': 1.0})

    def inc_category(self, cat):
        """カテゴリ cat が出現した回数を 1 増やす"""
        categories = self.db.categories.find({'user': self.user,
                                              'category': cat})
        if categories.count():
            self.db.categories.update({'user': self.user,
                                       'category': cat},
                                      {'$inc': {'count': 1}})
        else:
            self.db.categories.insert({'user': self.user,
                                       'category': cat,
                                       'count': 1})

    def get_feature_count(self, f, cat):
        """特徴 feature がカテゴリ cat に出現した回数を返す"""
        feature = self.db.features.find_one({'user': self.user,
                                             'feature': f,
                                             'category': cat})
        if feature:
            return float(feature['count'])
        else:
            return 0.0

    def get_cat_count(self, cat):
        """カテゴリ cat が出現した回数を返す"""
        category = self.db.categories.find_one({'user': self.user,
                                                'category': cat})
        if category:
            return category['count']
        else:
            return 0

    def total_count(self):
        """すべてのカテゴリの出現回数を返す"""
        r = self.db.categories.aggregate([
            {'$group': {'_id': None,
             'total': {'$sum': '$count'}}}
        ])
        return r['result'][0]['total']

    def categories(self):
        """すべてのカテゴリのリストを返す"""
        return map(lambda x: x['category'],
                   self.db.categories.find({'user': self.user}))

    def commit(self):
        """学習結果を保存する"""
        pass


class Classifier(object):
    def __init__(self, get_features, backend):
        self.get_features = get_features
        self.backend = backend

    def inc_feature(self, f, cat):
        """特徴 feature がカテゴリ cat に出現した回数を 1 増やす"""
        self.backend.inc_feature(f, cat)

    def inc_category(self, cat):
        """カテゴリ cat が出現した回数を 1 増やす"""
        self.backend.inc_category(cat)

    def get_feature_count(self, f, cat):
        """特徴 feature がカテゴリ cat に出現した回数を返す"""
        return self.backend.get_feature_count(f, cat)

    def get_cat_count(self, cat):
        """カテゴリ cat が出現した回数を返す"""
        return self.backend.get_cat_count(cat)

    def total_count(self):
        """すべてのカテゴリの出現回数を返す"""
        return self.backend.total_count()

    def categories(self):
        """すべてのカテゴリのリストを返す"""
        return self.backend.categories()

    def train(self, item, cat):
        """アイテム item がカテゴリ cat に出現したことを学習する"""
        features = self.get_features(item)
        for f in features:
            self.inc_feature(f, cat)
        self.inc_category(cat)
        self.backend.commit()

    def feature_prob(self, feature, cat):
        """カテゴリ cat において特徴 feature が出現する確率を返す"""
        cat_count = self.get_cat_count(cat)
        if cat_count == 0:
            return 0.0
        else:
            feature_count = self.get_feature_count(feature, cat)
            return float(feature_count) / cat_count

    def weighted_prob(self, feature, basic_prob, weight=1.0, ap=0.5):
        """特徴 feature の出現頻度が低い場合の確率を補正する"""

        # 特徴 feature がすべてのカテゴリに出現した回数の合計
        totals = sum([self.get_feature_count(feature, c)
                      for c in self.categories()])

        # 重み付き平均を取る
        return ((weight * ap) + (totals * basic_prob)) / (weight + totals)


class NaiveBayesClassifier(Classifier):
    """単純ベイズ法による分類機"""

    def __init__(self, get_features, backend):
        super(NaiveBayesClassifier, self).__init__(get_features, backend)
        self.thresholds = {}

    def get_threshold(self, cat):
        return self.thresholds.get(cat, 1.0)

    def set_threshold(self, cat, t):
        self.thresholds[cat] = t

    def doc_prob(self, item, cat):
        """Pr(item | cat) を求める"""
        p = 1
        for feature in self.get_features(item):
            basic_prob = self.feature_prob(feature, cat)
            p *= self.weighted_prob(feature, basic_prob)
        return p

    def prob(self, item, cat):
        return self.bayes_prob(item, cat)

    def bayes_prob(self, item, cat):
        """Pr(item | cat) * Pr(cat) を求める

        この値は Pr(cat | item) に比例する:

          Pr(item | cat) * Pr(cat) = Pr(cat | item) * Pr(item)

        ここで Pr(item) は cat によらず一定
        """
        cat_prob = float(self.get_cat_count(cat)) / self.total_count()
        doc_prob = self.doc_prob(item, cat)
        return doc_prob * cat_prob

    def classify(self, item, default=None):
        """アイテム item が属す確率が最も高いカテゴリを選択する"""
        probs = {}
        max = 0.0
        best = default
        for cat in self.categories():
            probs[cat] = self.prob(item, cat)
            if probs[cat] > max:
                max = probs[cat]
                best = cat

        for cat in probs:
            if cat == best:
                continue
            if probs[cat] * self.get_threshold(best) > probs[best]:
                return default

        return best


class ComplementNaiveBayesClassifier(Classifier):
    """complement naive bayes 法による分類機"""

    def complement_doc_prob(self, item, cat):
        """Pr(item | cat 以外のカテゴリ) を求める"""
        p = 1.0
        for feature in self.get_features(item):
            feature_count = 0
            cat_count = 0
            for c in self.categories():
                if c != cat:
                    feature_count += self.get_feature_count(feature, c)
                    cat_count += self.get_cat_count(c)
            if cat_count == 0:
                basic_prob = 0.0
            else:
                basic_prob = float(feature_count) / cat_count
            p *= self.weighted_prob(feature, basic_prob)
        return p

    def prob(self, item, cat):
        return self.complement_bayes_prob(item, cat)

    def complement_bayes_prob(self, item, cat):
        """アイテム item が cat 以外のカテゴリに属する確率を求める"""
        cat_prob = float(self.get_cat_count(cat)) / self.total_count()
        doc_prob = self.complement_doc_prob(item, cat)
        return math.log(cat_prob) - math.log(doc_prob)

    def classify(self, item, default=None):
        """アイテム item が属さない確率が最も低いカテゴリを選択する"""
        best = default
        max = 0.0
        for cat in self.categories():
            prob = self.prob(item, cat)
            if prob > max:
                max = prob
                best = cat

        return best


class FisherClassifier(Classifier):
    """フィッシャー法による分類機"""

    def __init__(self, get_features, backend):
        super(FisherClassifier, self).__init__(get_features, backend)
        self.minimums = {}

    def get_minimum(self, cat):
        return self.minimums.get(cat, 0.0)

    def set_minimum(self, cat, min):
        self.minimums[cat] = min

    def cprob(self, feature, cat):
        """特徴 feature を持つアイテムがカテゴリ cat に属する確率を返す

        カテゴリ中のドキュメントの数が同数程度であると仮定している.
        """

        clf = self.feature_prob(feature, cat)
        if clf == 0:
            return 0

        freq_sum = sum([self.feature_prob(feature, c)
                        for c in self.categories()])

        return clf / freq_sum

    def prob(self, item, cat):
        return self.fisher_prob(item, cat)

    def fisher_prob(self, item, cat):
        """アイテム item がカテゴリ cat に属するスコアをフィッシャー法により求める"""
        p = 1
        features = self.get_features(item)
        for feature in features:
            basic_prob = self.cprob(feature, cat)
            p *= self.weighted_prob(feature, basic_prob)

        fscore = -2 * math.log(p)
        return self.invchi2(fscore, len(features) * 2)

    def invchi2(self, chi, dof):
        """カイ２乗の逆数を返す"""
        m = chi / 2.0
        sum = term = math.exp(-m)
        for i in xrange(1, dof // 2):
            term *= m / i
            sum += term
        return min(sum, 1.0)

    def classify(self, item, default=None):
        best = default
        max = 0.0
        for cat in self.categories():
            prob = self.prob(item, cat)
            if prob > max and prob > self.get_minimum(cat):
                best = cat
                max = prob

        return best


def sample_train(cl):
    cl.train("Nobody owns the water.", "good")
    cl.train("the quick rabbit jumps fences", "good")
    cl.train("buy pharmaceuticals now", "bad")
    cl.train("make quick money in the online casino", "bad")
    cl.train("the quick brown fox jumps", "good")
