package scraper

import (
	"context"
	"errors"
	"os"
	"path"
	"regexp"
	"strconv"
	"strings"
	"time"

	"github.com/Zogwine/Zogwine/internal/database"
	"github.com/Zogwine/Zogwine/internal/file"
	"github.com/Zogwine/Zogwine/internal/scraper/common"
	"github.com/Zogwine/Zogwine/internal/status"
	"github.com/Zogwine/Zogwine/internal/util"
	log "github.com/sirupsen/logrus"
)

type TVSScraper struct {
	MediaType     database.MediaType
	IDLib         int64
	LibPath       string
	AutoAdd       bool
	AddUnknown    bool
	App           *status.Status
	Providers     map[string]common.TVShowProvider
	ProviderNames []string // list used to keep the order of preferences
	RegexSeason   *regexp.Regexp
	RegexEpisode  *regexp.Regexp
}

func (t *TVSScraper) getProviderFromName(pname string) (common.TVShowProvider, error) {
	for name, prov := range t.Providers {
		if name == pname {
			return prov, nil
		}
	}
	return nil, errors.New("provider " + pname + " not found")
}

func (t *TVSScraper) loadTVSPlugins() error {
	names, config, err := ListScraperConfiguration(t.App, database.MediaTypeTvs)

	if err != nil {
		return err
	}

	for _, i := range names {
		pl, err := util.LoadPlugin("TVShowProvider", "./plugins/scraper/"+i)
		if err == nil {
			p, ok := pl.(func() common.TVShowProvider)
			if ok {
				t.Providers[i] = p()
				t.Providers[i].Setup(config[i], t.App.Log)
				t.ProviderNames = append(t.ProviderNames, i)
			}
		}
	}

	t.App.Log.WithFields(log.Fields{"entity": "scraper", "file": "tvshow", "function": "loadTVSPlugins"}).Info("loaded providers: " + strings.Join(t.ProviderNames, ","))

	if len(t.Providers) == 0 {
		return errors.New("no provider loaded")
	}

	return nil
}

func NewTVSScraper(s *status.Status) TVSScraper {
	seasonReg, _ := regexp.Compile("(?i)(?:s)(\\d+)(?:e)")
	epReg, _ := regexp.Compile("(?i)(?:s\\d+e)(\\d+)")
	t := TVSScraper{MediaType: database.MediaTypeTvs, IDLib: 0, AutoAdd: false, AddUnknown: true, App: s, Providers: map[string]common.TVShowProvider{}, ProviderNames: []string{}, RegexSeason: seasonReg, RegexEpisode: epReg}
	err := t.loadTVSPlugins()
	if err != nil {
		t.App.Log.WithFields(log.Fields{"entity": "scraper", "file": "tvshow", "function": "NewTVSScraper"}).Warn(err)
	}
	return t
}

func (t *TVSScraper) Scan(idlib int64, AutoAdd bool, AddUnknown bool) error {
	t.IDLib = idlib
	t.AutoAdd = AutoAdd
	t.AddUnknown = AddUnknown
	ctx := context.Background()

	// get library base path
	lib, err := t.App.DB.GetLibrary(ctx, t.IDLib)
	if err != nil {
		return errors.New("unable to retreive library path: " + err.Error())
	}
	t.LibPath = lib.Path

	// get data for existing tvs
	tvsData, err := t.App.DB.ListShow(ctx, 0)
	if err != nil {
		return err
	}

	tvsPaths := []string{}
	for _, i := range tvsData {
		tvsPaths = append(tvsPaths, i.Path)
	}

	// list items at this path
	items, err := os.ReadDir(t.LibPath)
	if err != nil {
		return err
	}

	for _, i := range items {
		if i.IsDir() {
			// keep only the folders
			currentShow := util.Index(tvsPaths, i.Name())
			logF := log.Fields{"entity": "scraper", "file": "tvshow", "function": "Scan", "tvs": i.Name()}
			t.App.Log.WithFields(logF).Debugf("processing tvs: %s", currentShow)

			var data database.ListShowRow
			if currentShow > -1 {
				// if there is already an entry for this tvs
				t.App.Log.WithFields(logF).Trace("tvs already in database")
				data = tvsData[currentShow]
				if data.UpdateMode > 0 {
					// if updates are allowed
					if data.ScraperID == "" || data.ScraperName == "" || data.ScraperName == " " {
						// if no scraper is associated to this tvs, just re-run a search
						t.App.Log.WithFields(logF).Trace("add tvs")
						data, err = t.addTVS(data)
					} else {
						// else, update tvs metadata
						t.App.Log.WithFields(logF).Trace("update tvs")
						data, err = t.updateTVS(data)
					}
				} else {
					t.App.Log.WithFields(logF).Trace("no update needed")
				}
			} else {
				// if this is a newly discovered tvs
				t.App.Log.WithFields(logF).Trace("new tvs: " + i.Name())
				data.Title = i.Name()
				data, err = t.addTVS(data)
			}

			if err != nil && data.ScraperID != "" {
				// if a scraper is associated, update episodes
				t.App.Log.WithFields(logF).Trace("update episodes")
				t.updateTVSEpisodes(data)
			}

			if err != nil {
				t.App.Log.WithFields(logF).Error(err)
			}
		}
	}

	return nil
}

func (t *TVSScraper) addTVS(data database.ListShowRow) (database.ListShowRow, error) {
	searchResults := []common.SearchData{}
	var err error

	// retreive search results for each provider
	for _, i := range t.ProviderNames {
		res, err := t.Providers[i].SearchTVS(data.Title)
		if err == nil {
			searchResults = append(searchResults, res...)
		}
	}

	if len(searchResults) == 0 && !t.AddUnknown {
		return data, errors.New("no data avaiable for show " + data.Title)
	}

	if data.ID == 0 {
		// if this is a new tvs
		// create a new entry in the database
		data.ID, err = t.App.DB.AddShow(context.Background(), database.AddShowParams{
			Title:   data.Title,
			IDLib:   t.IDLib,
			AddDate: time.Now().Unix(),
		})
		if err != nil {
			return data, err
		}
	}

	if t.AutoAdd {
		// if we want to try to automatically select the best result
		selected, err := SelectBestItem(searchResults, data.Title, 0)
		if err == nil {
			// if a result was selected
			t.UpdateWithSelectionResult(data.ID, SelectionResult{ScraperName: selected.ScraperName, ScraperID: selected.ScraperID, ScraperData: selected.ScraperData})
			data.ScraperID = selected.ScraperID
			data.ScraperName = selected.ScraperName
			data.ScraperData = selected.ScraperData
			// force tvs update
			return t.updateTVS(data)
		} else {
			AddMultipleResults(t.App, database.MediaTypeTvs, data.ID, searchResults)
		}
	} else {
		AddMultipleResults(t.App, database.MediaTypeTvs, data.ID, searchResults)
	}

	return data, nil
}

// update tvs, tags and people metadata
func (t *TVSScraper) updateTVS(data database.ListShowRow) (database.ListShowRow, error) {
	ctx := context.Background()
	provider, err := t.getProviderFromName(data.ScraperName)
	if err != nil {
		return data, err
	}
	provider.Configure(data.ScraperID, data.ScraperData)

	// update tvs metadata
	tvsData, err := provider.GetTVS()
	if err != nil {
		return data, err
	}
	err = t.App.DB.UpdateShow(ctx, database.UpdateShowParams{
		Title:       tvsData.Title,
		Overview:    tvsData.Overview,
		Icon:        tvsData.Icon,
		Fanart:      tvsData.Fanart,
		Website:     tvsData.Website,
		Trailer:     tvsData.Trailer,
		Premiered:   tvsData.Premiered,
		Rating:      tvsData.Rating,
		ScraperLink: tvsData.ScraperInfo.ScraperLink,
		ScraperData: tvsData.ScraperInfo.ScraperData,
		UpdateDate:  time.Now().Unix(),
		ID:          data.ID,
	})
	if err != nil {
		return data, err
	}
	data.Title = tvsData.Title
	data.ScraperData = tvsData.ScraperInfo.ScraperData
	data.Premiered = tvsData.Premiered

	// update tags
	tagData, err := provider.ListTVSTag()
	if err != nil {
		return data, err
	}
	for _, i := range tagData {
		AddTag(t.App, database.MediaTypeTvs, data.ID, i)
	}

	// update people
	persData, err := provider.ListTVSPerson()
	if err != nil {
		return data, err
	}
	for _, i := range persData {
		AddPerson(t.App, database.MediaTypeTvs, data.ID, i)
	}

	return data, nil
}

// update tvs seasons and episodes metadata
func (t *TVSScraper) updateTVSEpisodes(data database.ListShowRow) error {
	ctx := context.Background()
	logF := log.Fields{"entity": "scraper", "file": "tvshow", "function": "updateTVSEpisodes", "tvs": data.Title}

	// get path to the root tvs folder
	tvsPath := path.Join(t.LibPath, data.Path)

	// get provider
	provider, err := t.getProviderFromName(data.ScraperName)
	if err != nil {
		return err
	}
	provider.Configure(data.ScraperID, data.ScraperData)

	// list existing seasons
	seasonData, err := t.App.DB.ListShowSeason(ctx, database.ListShowSeasonParams{IDUser: 0, IDShow: data.ID})
	if err != nil {
		return err
	}
	seasons := []int64{}
	for _, i := range seasonData {
		if i.UpdateMode > 0 {
			// update the seasons if needed
			seasonData, err := provider.GetTVSSeason(int(i.Season))
			if err == nil {
				t.App.DB.UpdateShowSeason(ctx, database.UpdateShowSeasonParams{
					Title:       seasonData.Title,
					Overview:    seasonData.Overview,
					Icon:        seasonData.Icon,
					Season:      i.Season,
					Fanart:      seasonData.Fanart,
					Premiered:   seasonData.Premiered,
					Rating:      seasonData.Rating,
					Trailer:     seasonData.Trailer,
					ScraperName: seasonData.ScraperInfo.ScraperName,
					ScraperData: seasonData.ScraperInfo.ScraperData,
					ScraperID:   seasonData.ScraperInfo.ScraperID,
					ScraperLink: seasonData.ScraperInfo.ScraperLink,
					UpdateDate:  time.Now().Unix(),
					UpdateMode:  0,
				})
			} else {
				t.App.Log.WithFields(logF).Error(err)
			}
		}

		seasons = append(seasons, i.Season)
	}

	// for each file in the tvs folder
	for _, i := range ListFiles(tvsPath) {
		p := path.Join(tvsPath, i)

		videoData, err := t.App.DB.GetVideoFileFromPath(ctx, database.GetVideoFileFromPathParams{IDLib: t.IDLib, Path: i})
		if err == nil {
			episodeData, err := t.App.DB.GetShowEpisode(ctx, database.GetShowEpisodeParams{IDUser: 0, ID: videoData.MediaData})
			if err == nil && episodeData.UpdateMode > 0 {
				err = file.UpdateVideoFile(t.App, t.IDLib, p)
				epData, err := provider.GetTVSEpisode(int(episodeData.Season), int(episodeData.Episode))
				if err == nil {
					t.App.DB.UpdateShowEpisode(ctx, database.UpdateShowEpisodeParams{
						Title:       epData.Title,
						Overview:    epData.Overview,
						Icon:        epData.Icon,
						Premiered:   epData.Premiered,
						Rating:      epData.Rating,
						ScraperID:   epData.ScraperInfo.ScraperID,
						ScraperName: epData.ScraperInfo.ScraperName,
						ScraperData: epData.ScraperInfo.ScraperData,
						ScraperLink: epData.ScraperInfo.ScraperLink,
						UpdateDate:  time.Now().Unix(),
						UpdateMode:  0,
					})
				} else {
					t.App.Log.WithFields(logF).Error(err)
				}
			} else {
				t.App.Log.WithFields(logF).Error(err)
			}

		} else {
			// if there are no existing entries for this episodes

			// extract season and episode number from filename
			searchStr := []byte(path.Base(i))
			searchSeason := t.RegexSeason.Find(searchStr)
			searchEpisode := t.RegexEpisode.Find(searchStr)

			if searchSeason != nil && searchEpisode != nil {
				season, _ := strconv.Atoi(string(searchSeason))
				episode, _ := strconv.Atoi(string(searchEpisode))

				if err == nil {
					if !util.Contains(seasons, int64(season)) {
						// if the season is unknown, add it
						seasonData, err := provider.GetTVSSeason(season)
						if err == nil {
							t.App.DB.AddShowSeason(ctx, database.AddShowSeasonParams{
								Title:       seasonData.Title,
								Overview:    seasonData.Overview,
								Icon:        seasonData.Icon,
								Season:      int64(season),
								Fanart:      seasonData.Fanart,
								Premiered:   seasonData.Premiered,
								Rating:      seasonData.Rating,
								Trailer:     seasonData.Trailer,
								ScraperName: seasonData.ScraperInfo.ScraperName,
								ScraperData: seasonData.ScraperInfo.ScraperData,
								ScraperID:   seasonData.ScraperInfo.ScraperID,
								ScraperLink: seasonData.ScraperInfo.ScraperLink,
								AddDate:     time.Now().Unix(),
								UpdateMode:  0,
							})
						} else {
							t.App.Log.WithFields(logF).Error(err)
						}
						seasons = append(seasons, int64(season))
					}

					// add the episode
					epData, err := provider.GetTVSEpisode(season, episode)
					if err == nil {
						idEp, err := t.App.DB.AddShowEpisode(ctx, database.AddShowEpisodeParams{
							Title:       epData.Title,
							Overview:    epData.Overview,
							Icon:        epData.Icon,
							Premiered:   epData.Premiered,
							Rating:      epData.Rating,
							Season:      epData.Season,
							Episode:     epData.Episode,
							ScraperName: epData.ScraperInfo.ScraperName,
							ScraperID:   epData.ScraperInfo.ScraperID,
							ScraperData: epData.ScraperInfo.ScraperData,
							ScraperLink: epData.ScraperInfo.ScraperLink,
							AddDate:     time.Now().Unix(),
							UpdateMode:  0,
						})
						if err == nil {
							file.AddVideoFile(t.App, t.IDLib, p, database.MediaTypeTvsEpisode, idEp, false)
						} else {
							t.App.Log.WithFields(logF).Error(err)
						}
					} else if t.AddUnknown {
						t.App.Log.WithFields(logF).Warn("no data found for s" + strconv.Itoa(season) + "e" + strconv.Itoa(episode) + ", adding empty val")
						// if no data is found but addUnknown is enabled
						idEp, err := t.App.DB.AddShowEpisode(ctx, database.AddShowEpisodeParams{
							Title:      i,
							AddDate:    time.Now().Unix(),
							UpdateMode: 0,
						})
						if err == nil {
							file.AddVideoFile(t.App, t.IDLib, p, database.MediaTypeTvsEpisode, idEp, false)
						} else {
							t.App.Log.WithFields(logF).Error(err)
						}
					} else {
						t.App.Log.WithFields(logF).Warn("no data found for s" + strconv.Itoa(season) + "e" + strconv.Itoa(episode))
					}
				}
			} else {
				t.App.Log.WithFields(logF).Warn("unable to extract season/episode info for: " + string(searchStr))
			}
		}
	}

	return nil
}

func (t *TVSScraper) UpdateWithSelectionResult(id int64, selection SelectionResult) error {
	ctx := context.Background()
	// update tvs
	err := t.App.DB.UpdateShow(ctx, database.UpdateShowParams{ScraperID: selection.ScraperID, ScraperName: selection.ScraperName, ScraperData: selection.ScraperData, UpdateMode: 1, ID: id})
	if err != nil {
		return err
	}
	// purge outdated data
	// force rescan of seasons and episodes
	err = t.App.DB.UpdateShowAllSeasons(ctx, database.UpdateShowAllSeasonsParams{IDShow: id, ScraperName: " ", ScraperID: "0", UpdateMode: 1})
	if err != nil {
		return err
	}
	err = t.App.DB.UpdateShowAllEpisodes(ctx, database.UpdateShowAllEpisodesParams{IDShow: id, ScraperName: " ", ScraperID: "0", UpdateMode: 1})
	if err != nil {
		return err
	}
	// delete tags and people
	err = t.App.DB.DeleteAllTagLinks(ctx, database.DeleteAllTagLinksParams{MediaType: database.MediaTypeTvs, MediaData: id})
	if err != nil {
		return err
	}
	err = t.App.DB.DeleteAllPersonLinks(ctx, database.DeleteAllPersonLinksParams{MediaType: database.MediaTypeTvs, MediaData: id})
	if err != nil {
		return err
	}
	return nil
}
