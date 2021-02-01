#include "stdafx.h"
#include "cryptmanager.h"
#include "mainwindow.h"
#include "messagewindow.h"
#include "homewidget.h"
#include "settingwidget.h"
#include "scriptwidget.h"
#include "logwidget.h"

HomeWidget* g_pHomeWidget = NULL;
SettingWidget* g_pSettingWidget = NULL;
ScriptWidget* g_pScriptWidget = NULL;
LogWidget* g_pLogWidget = NULL;

QString g_token;
QMutex g_mutex;
std::shared_ptr<spdlog::logger> g_logger;
std::list<std::pair<DWORD, TimerProcesser> > g_delayExec;
UINT_PTR g_delayTimerID = NULL;

int g_interval = 0;
std::string g_phone;
USHORT g_port = 0;
std::string g_sync;
int g_tbExpire = 0;
unsigned __int64 g_tbUserId = 0;
std::string g_tbUserName;
std::string g_tbCode;

std::string g_func;
std::string g_script;
std::string g_custom;
std::string g_officials;	//filehelper,qmessage,fmessage,tmessage,qqmail,medianote,floatbottle,weibo,weixin,mphelper,gh_7aac992b0363,gh_3dfda90e39d6
std::map<std::string, std::string> g_blackMap;
std::map<std::string, std::string> g_whiteMap;
MyAbstractTableModel* g_pBlackTableModel;
MyAbstractTableModel* g_pWhiteTableModel;

std::string g_currentWxid;
int g_currentPage;
lua_State* g_pLua = NULL;
QMap<std::string, int> g_connMap;
QMap<std::string, std::string> g_folderMap;
QMap<std::string, SQLite::Database*> g_dbMap;

//QMap<std::string, std::string> g_folderMap;
//QMap<std::string, lua_State*> g_luaMap;
//QMap<std::string, Json::Value> g_wechatInfoMaps;
//QMap<std::string, Json::Value> g_contactInfoMaps;
//QMap<std::string, Json::Value> g_groupInfoMaps;


QDateTime g_serverDate;
QDateTime g_terminateDate;
MainWindow* g_pMainWindow = NULL;
ITcpPackServer* g_pTcpPackServer = NULL;


BOOL MySendPack(DWORD conn, DWORD flag, Json::Value& root)
{
	VMP_PROTECT_START;

	//Json::StyledWriter格式化的
	Json::FastWriter fastWriter;
	std::string data = fastWriter.write(root);

	data = CryptManager::EncodeAesString(data);

	int size = data.size() + 4;

	BYTE* buffer = new BYTE[size];
	memcpy(buffer, &flag, 4);
	memcpy(buffer + 4, data.c_str(), data.size());

	BOOL ret = g_pTcpPackServer->Send(conn, buffer, size);

	delete buffer;

	return ret;

	VMP_PROTECT_END;
}

BOOL MyRecvPack(const BYTE* pData, int len, Json::Value& root)
{
	VMP_PROTECT_START;

	std::string data = std::string((char*)(pData + 4), len - 4);
	data = CryptManager::DecodeAesString(data);

	Json::Reader reader;
	return reader.parse(data, root);

	VMP_PROTECT_END;
}


void DelayExec(const TimerProcesser &func, int delayTime, bool unique)
{
	if (delayTime <= 0)
	{
		func();
	}
	else
	{
		if (unique)
		{
			for (auto it = g_delayExec.begin(); it != g_delayExec.end(); ++it)
			{
				// Duplicated function
				if (DWORD(it->second.functor.func_ptr) == DWORD(func.functor.func_ptr))	//if (DWORD(it->second.functor.members.func_ptr) == DWORD(func.functor.members.func_ptr))
				{
					return;
				}
			}
		}

		DWORD nextDelayTime = GetTickCount() + delayTime;
		if (g_delayExec.empty())
		{
			g_delayExec.push_back(std::make_pair(nextDelayTime, func));
		}
		else
		{
			// Get function that delay time less than nextDelayTime
			auto findIt = find_if(g_delayExec.begin(), g_delayExec.end(), boost::bind(std::less<DWORD>(), nextDelayTime, boost::bind(&std::pair<DWORD, boost::function<void()> >::first, _1)));

			g_delayExec.insert(findIt, std::make_pair(nextDelayTime, func));
		}
	}
}

void CALLBACK DelayExecTimer(HWND hWnd, UINT nMsg, UINT nTimerid, DWORD dwTime)
{
	DWORD ct = GetTickCount();

	auto find_it = find_if(g_delayExec.begin(), g_delayExec.end(), boost::bind(std::less<DWORD>(), ct, boost::bind(&std::pair<DWORD, TimerProcesser>::first, _1)));

	std::list<TimerProcesser> fs;
	for (auto it = g_delayExec.begin(); it != find_it; ++it)
	{
		fs.push_back(it->second);
	}

	g_delayExec.erase(g_delayExec.begin(), find_it);
	for (auto it = fs.begin(); it != fs.end(); ++it)
	{
		try
		{
			(*it)();
		}
		catch (...) {}
	}

#ifdef NDEBUG
	VMP_PROTECT_START;
	//检测调试器
	if (IsDebuggerPresent())
	{
		KillTimer(NULL, g_delayTimerID);
		exit(0);
	}
	VMP_PROTECT_END;
#endif
}

int my_trace(CURL *handle, curl_infotype type, char *data, size_t size, void *userp)
{
	char* text = NULL;

	switch (type)
	{
	case CURLINFO_TEXT:
		text = data;
		break;
	case CURLINFO_HEADER_OUT:
		text = "=> Send header";
		break;
	case CURLINFO_DATA_OUT:
		text = "=> Send data";
		break;
	case CURLINFO_HEADER_IN:
		text = "<= Recv header";
		break;
	case CURLINFO_DATA_IN:
		text = "<= Recv data";
		break;
	default: /* in case a new one is introduced to shock us */
		return 0;
	}
}

size_t write_callback(char *buffer, size_t size, size_t nitems, std::string *userp)
{
	if (userp == NULL)
	{
		return 0;
	}

	unsigned long written = size * nitems;
	userp->append(buffer, written);
	return written;
}

size_t file_callback(void *ptr, size_t size, size_t nmemb, FILE *stream)
{
	if (stream == NULL)
	{
		return 0;
	}

	size_t written = fwrite(ptr, size, nmemb, stream);
	return written;
}

CURLcode CheckFile(std::string url, double* size)
{
	CURLcode res;

	CURL* curl = curl_easy_init();
	if (curl)
	{
		struct curl_slist *headers = NULL;
		//headers = curl_slist_append(headers, std::string("User-Agent: wget").c_str());

		curl_easy_setopt(curl, CURLOPT_URL, url.c_str());
		curl_easy_setopt(curl, CURLOPT_SSL_VERIFYPEER, 0);
		curl_easy_setopt(curl, CURLOPT_SSL_VERIFYHOST, 0);
		curl_easy_setopt(curl, CURLOPT_FOLLOWLOCATION, 1);
		curl_easy_setopt(curl, CURLOPT_HTTPHEADER, headers);
		curl_easy_setopt(curl, CURLOPT_TIMEOUT_MS, ONE_MINUTE);

		//curl_easy_setopt(curl, CURLOPT_HEADER, 1);	//是否获取HTTP头信息
		//curl_easy_setopt(curl, CURLOPT_HEADERDATA, header);
		//curl_easy_setopt(curl, CURLOPT_HEADERFUNCTION, write_callback);


		curl_easy_setopt(curl, CURLOPT_NOBODY, 1);
		curl_easy_setopt(curl, CURLOPT_POST, 0);
		curl_easy_setopt(curl, CURLOPT_VERBOSE, 1);
		//curl_easy_setopt(curl, CURLOPT_COOKIEJAR, "cookie.txt");
		//curl_easy_setopt(curl, CURLOPT_COOKIEFILE, "cookie.txt");

		/* Perform the request, res will get the return code */
		res = curl_easy_perform(curl);

		res = curl_easy_getinfo(curl, CURLINFO_CONTENT_LENGTH_DOWNLOAD, size);

		long responseCode = 0;
		res = curl_easy_getinfo(curl, CURLINFO_RESPONSE_CODE, &responseCode);
		if (responseCode != 200)
		{
			*size = -1;
		}

		/* always cleanup */
		curl_slist_free_all(headers);

		curl_easy_cleanup(curl);
	}

	return res;
}

CURLcode DownFile(std::string url, std::string file)
{
	CURLcode res;

	CURL* curl = curl_easy_init();
	if (curl)
	{
		FILE* fp = fopen(file.c_str(), "wb");

		struct curl_slist *headers = NULL;
		//headers = curl_slist_append(headers, std::string("User-Agent: wget").c_str());

		curl_easy_setopt(curl, CURLOPT_URL, url.c_str());
		curl_easy_setopt(curl, CURLOPT_SSL_VERIFYPEER, 0);
		curl_easy_setopt(curl, CURLOPT_SSL_VERIFYHOST, 0);
		curl_easy_setopt(curl, CURLOPT_FOLLOWLOCATION, 1);
		curl_easy_setopt(curl, CURLOPT_HTTPHEADER, headers);
		curl_easy_setopt(curl, CURLOPT_TIMEOUT_MS, TEN_MINUTES);

		//curl_easy_setopt(curl, CURLOPT_HEADER, 1);	//是否获取HTTP头信息
		//curl_easy_setopt(curl, CURLOPT_HEADERDATA, header);
		//curl_easy_setopt(curl, CURLOPT_HEADERFUNCTION, write_callback);  

		curl_easy_setopt(curl, CURLOPT_WRITEDATA, fp);
		curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, file_callback);
		curl_easy_setopt(curl, CURLOPT_NOBODY, 0);
		curl_easy_setopt(curl, CURLOPT_POST, 0);
		//curl_easy_setopt(curl, CURLOPT_VERBOSE, 1);
		//curl_easy_setopt(curl, CURLOPT_COOKIEJAR, "cookie.txt");
		//curl_easy_setopt(curl, CURLOPT_COOKIEFILE, "cookie.txt");

		/* Perform the request, res will get the return code */
		res = curl_easy_perform(curl);

		/* always cleanup */
		curl_slist_free_all(headers);

		curl_easy_cleanup(curl);

		fclose(fp);
	}

	return res;
}

CURLcode GetUrl(std::string url, std::string* buffer)
{
	CURLcode res;

	CURL* curl = curl_easy_init();
	if (curl)
	{
		struct curl_slist *headers = NULL;
		//headers = curl_slist_append(headers, std::string("User-Agent: wget").c_str());
		//headers = curl_slist_append(headers, "Content-Type: application/json; charset=GB2312");

		curl_easy_setopt(curl, CURLOPT_URL, url.c_str());
		curl_easy_setopt(curl, CURLOPT_SSL_VERIFYPEER, 0);
		curl_easy_setopt(curl, CURLOPT_SSL_VERIFYHOST, 0);
		curl_easy_setopt(curl, CURLOPT_FOLLOWLOCATION, 1);
		curl_easy_setopt(curl, CURLOPT_HTTPHEADER, headers);
		curl_easy_setopt(curl, CURLOPT_TIMEOUT_MS, ONE_MINUTE);

		//curl_easy_setopt(curl, CURLOPT_HEADER, 1);	//是否获取HTTP头信息
		//curl_easy_setopt(curl, CURLOPT_HEADERDATA, header);
		//curl_easy_setopt(curl, CURLOPT_HEADERFUNCTION, write_callback);  

		curl_easy_setopt(curl, CURLOPT_WRITEDATA, buffer);
		curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, write_callback);

		curl_easy_setopt(curl, CURLOPT_POST, 0);

		//curl_easy_setopt(curl, CURLOPT_DEBUGFUNCTION, my_trace);
		//curl_easy_setopt(curl, CURLOPT_VERBOSE, 1);
		//curl_easy_setopt(curl, CURLOPT_STDERR, file);

		//curl_easy_setopt(curl, CURLOPT_COOKIEJAR, "cookie.txt");
		//curl_easy_setopt(curl, CURLOPT_COOKIEFILE, "cookie.txt");

		/* Perform the request, res will get the return code */
		res = curl_easy_perform(curl);

		/* always cleanup */
		curl_slist_free_all(headers);
	}

	curl_easy_cleanup(curl);

	return res;
}

CURLcode PostUrl(std::string url, std::string args, std::string* buffer)
{
	CURLcode res;

	CURL* curl = curl_easy_init();
	if (curl)
	{
		struct curl_slist *headers = NULL;
		//headers = curl_slist_append(headers, std::string("User-Agent: wget").c_str());
		//headers = curl_slist_append(headers, "Content-Type: application/json; charset=GB2312");

		curl_easy_setopt(curl, CURLOPT_URL, url.c_str());
		curl_easy_setopt(curl, CURLOPT_SSL_VERIFYPEER, 0);
		curl_easy_setopt(curl, CURLOPT_SSL_VERIFYHOST, 0);
		curl_easy_setopt(curl, CURLOPT_FOLLOWLOCATION, 1);
		curl_easy_setopt(curl, CURLOPT_HTTPHEADER, headers);
		curl_easy_setopt(curl, CURLOPT_TIMEOUT_MS, ONE_MINUTE);

		//curl_easy_setopt(curl, CURLOPT_HEADER, 1);	//是否获取HTTP头信息
		//curl_easy_setopt(curl, CURLOPT_HEADERDATA, header);
		//curl_easy_setopt(curl, CURLOPT_HEADERFUNCTION, write_callback);  

		curl_easy_setopt(curl, CURLOPT_WRITEDATA, buffer);
		curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, write_callback);

		curl_easy_setopt(curl, CURLOPT_POST, 1);
		curl_easy_setopt(curl, CURLOPT_POSTFIELDS, args.c_str());

		//curl_easy_setopt(curl, CURLOPT_DEBUGFUNCTION, my_trace);
		//curl_easy_setopt(curl, CURLOPT_VERBOSE, 1);
		//curl_easy_setopt(curl, CURLOPT_STDERR, file);

		//curl_easy_setopt(curl, CURLOPT_COOKIEJAR, "cookie.txt");
		//curl_easy_setopt(curl, CURLOPT_COOKIEFILE, "cookie.txt");

		/* Perform the request, res will get the return code */
		res = curl_easy_perform(curl);

		/* always cleanup */
		curl_slist_free_all(headers);

		curl_easy_cleanup(curl);
	}

	return res;
}



std::string EncodeBase64(std::string text)
{
	std::string result;

	result = CryptManager::EncodeBase64String(text);

	return result;
}

std::string DecodeBase64(std::string text)
{
	std::string result;

	result = CryptManager::DecodeBase64String(text);

	return result;
}

std::string EncodeRsaString(std::string text)
{
	std::string result;

	//result = CryptManager::EncodeRsaString(text);

	return result;
}

std::string DecodeRsaString(std::string text)
{
	 std::string result;

	//result = CryptManager::DecodeRsaString(text);

	return result;
}

std::string EncodeDesString(std::string text)
{
	std::string result;

	result = CryptManager::EncodeDesString(text);

	return result;
}

std::string DecodeDesString(std::string text)
{
	std::string result;

	result = CryptManager::DecodeDesString(text);

	return result;
}

void AcceptFriend(std::string self, std::string encryptUsername, std::string ticket)
{
	Json::Value request;
	request["encrypt_user_name"] = encryptUsername;
	request["ticket"] = ticket;

	MySendPack(g_connMap.value(self), ACCEPT_FRIEND_FLAG, request);
}

void AddBlackUser(std::string userName, std::string nickName)
{
	g_blackMap[userName] = nickName;

	QMetaObject::invokeMethod(g_pSettingWidget, "addBlackUser", Qt::QueuedConnection, Q_ARG(QString, QString::fromStdString(userName)), Q_ARG(QString, QString::fromStdString(nickName)));

}

void AddWhiteUser(std::string userName, std::string nickName)
{
	g_whiteMap[userName] = nickName;

	QMetaObject::invokeMethod(g_pSettingWidget, "addWhiteUser", Qt::QueuedConnection, Q_ARG(QString, QString::fromStdString(userName)), Q_ARG(QString, QString::fromStdString(nickName)));
}

void AtMsg(std::string self, std::string roomName, std::string userName, std::string nickName, std::string text)
{
	Json::Value request;
	request["room_name"] = roomName;
	request["user_name"] = userName;
	request["text"] = text;
	request["nick_name"] = nickName;

	MySendPack(g_connMap.value(self), AT_MSG_FLAG, request);
}

void DelayAtMsg(std::string self, std::string roomName, std::string userName, std::string nickName, std::string text, float seconds)
{
	DelayExec(boost::bind(&AtMsg, self, roomName, userName, nickName, text), seconds * ONE_SECOND, false);
}

void DelayAcceptFriend(std::string self, std::string encryptUsername, std::string ticket, float seconds)
{
	DelayExec(boost::bind(&AcceptFriend, self, encryptUsername, ticket), seconds * ONE_SECOND, false);
}

void AddFriend(std::string self, std::string wxid, std::string remark)
{
	Json::Value request;
	request["user_name"] = wxid;
	request["remark"] = remark;

	MySendPack(g_connMap.value(self), ADD_FRIEND_FLAG, request);
}

void AddChatroomMember(std::string self, std::string roomid, std::string wxid)
{
	Json::Value request;
	request["room_name"] = roomid;
	request["user_name"] = wxid;

	MySendPack(g_connMap.value(self), ADD_CHATROOM_MEMBER_FLAG, request);
}

void DelayAddChatroomMember(std::string self, std::string roomid, std::string wxid, float seconds)
{
	DelayExec(boost::bind(&AddChatroomMember, self, roomid, wxid), seconds * ONE_SECOND, false);
}

void DelFriend(std::string self, std::string wxid)
{
	Json::Value request;
	request["user_name"] = wxid;

	MySendPack(g_connMap.value(self), DEL_FRIEND_FLAG, request);
}

void DelChatroomMember(std::string self, std::string roomid, std::string wxid)
{
	Json::Value request;
	request["room_name"] = roomid;
	request["user_name"] = wxid;

	MySendPack(g_connMap.value(self), DEL_CHATROOM_MEMBER_FLAG, request);
}

void DelayDelChatroomMember(std::string self, std::string roomid, std::string wxid, float seconds)
{
	DelayExec(boost::bind(&DelChatroomMember, self, roomid, wxid), seconds * ONE_SECOND, false);
}

void ClearLog()
{
	g_pMainWindow->EmptyLog();
}

void CloseWechat(std::string self)
{
	Json::Value request;

	MySendPack(g_connMap.value(self), CLOSE_WECHAT_FLAG, request);
}

std::string ConvertLink(std::string tbPid, std::string link, std::string& errMsg)
{
	std::string result;

	//QString url = QStringLiteral("http://weforward.xiaozhushou233.cn/index.php/index/index/passwordParsing?taobao_user_id=%1&password_content=%2&promosition_position_id=%3").arg(g_tbUserId).arg(token).arg(tbPid.c_str()).arg(linkOrToken.c_str());
	//std::string buffer;
	//CURLcode res = GetUrl(url.toStdString(), &buffer);
	//result = buffer;

	result = link;

	return result;
}

std::string ConvertToken(std::string tbPid, std::string token, std::string& errMsg)
{
	std::string result;

	QString url = QStringLiteral("http://weforward.xiaozhushou233.cn/index.php/index/index/passwordParsing?taobao_user_id=%1&password_content=%2&promosition_position_id=%3").arg(g_tbUserId).arg(token.c_str()).arg(tbPid.c_str());
	std::string buffer;
	CURLcode res = GetUrl(url.toStdString(), &buffer);
	
	Json::Value root;
	Json::Reader reader;
	if (reader.parse(buffer, root))
	{
		std::string code = root["code"].asString();
		std::string sub_msg = root["sub_msg"].asString();
		std::string url = root["url"].asString();
		std::string token = root["password_simple"].asString();

		qDebug() << token.c_str() << url.c_str() << code.c_str() << sub_msg.c_str();

		errMsg = sub_msg;
		result = token;
	}

	return result;
}

void DecryptDB(std::string self, std::string encryptDBPath, std::string decryptDBPath)
{
	Json::Value request;
	request["src_path"] = encryptDBPath;
	request["dst_path"] = decryptDBPath;

	MySendPack(g_connMap.value(self), DECRYPT_DB_FLAG, request);
}

void ExecuteJS(std::string self, std::string code)
{
	Json::Value request;
	request["code"] = code;

	MySendPack(g_connMap.value(self), EXECUTE_JS_FLAG, request);
}

void DelayExecuteJS(std::string self, std::string code, float seconds)
{
	DelayExec(boost::bind(&ExecuteJS, self, code), seconds * ONE_SECOND, false);
}

void ExecuteSql(std::string self, std::string sql, std::string db)
{
	Json::Value request;
	request["db"] = db;
	request["sql"] = sql;

	MySendPack(g_connMap.value(self), EXECUTE_SQL_FLAG, request);
}

void DelayExecuteSql(std::string self, std::string sql, std::string db, float seconds)
{
	DelayExec(boost::bind(&ExecuteSql, self, sql, db), seconds * ONE_SECOND, false);
}

void OpenUrl(std::string self, std::string url)
{
	Json::Value request;
	request["url"] = url;

	MySendPack(g_connMap.value(self), OPEN_URL_FLAG, request);
}

void DecodeImg(std::string self, std::string srcPath, std::string dstPath)
{
	Json::Value request;
	request["src_path"] = srcPath;
	request["dst_path"] = dstPath;

	MySendPack(g_connMap.value(self), DECODE_IMG_FLAG, request);
}

void DownImg(std::string self, std::string wxid, std::string roomid, std::string xml, std::string path)
{
	Json::Value request;
	request["user_name"] = wxid;
	request["file_path"] = path;
	request["img_xml"] = xml;

	MySendPack(g_connMap.value(self), DOWN_IMG_FLAG, request);
}

void DelayOpenUrl(std::string self, std::string url, float seconds)
{
	DelayExec(boost::bind(&OpenUrl, self, url), seconds * ONE_SECOND, false);
}

void SyncMsg(std::string self)
{
	Json::Value request;

	MySendPack(g_connMap.value(self), SYNC_MSG_FLAG, request);
}

void DelaySyncMsg(std::string self, float seconds)
{
	DelayExec(boost::bind(&SyncMsg, self), seconds * ONE_SECOND, false);
}

void QueryContact(std::string self)
{
	Json::Value request;

	MySendPack(g_connMap.value(self), QUERY_CONTACT_FLAG, request);
}

void QueryGroup(std::string self)
{
	Json::Value request;

	MySendPack(g_connMap.value(self), QUERY_GROUP_FLAG, request);
}

void QueryMember(std::string self, std::string roomName)
{
	Json::Value request;
	request["room_name"] = roomName;

	MySendPack(g_connMap.value(self), QUERY_MEMBER_FLAG, request);
}

void QueryRepeat(std::string self)
{
	Json::Value request;

	MySendPack(g_connMap.value(self), QUERY_REPEAT_FLAG, request);
}

void QuerySelect(std::string self)
{
	Json::Value request;

	MySendPack(g_connMap.value(self), QUERY_SELECT_FLAG, request);
}

void QueryStats(std::string self, std::string roomName, std::string userList)
{
	Json::Value request;
	request["room_name"] = roomName;
	request["user_list"] = userList;

	MySendPack(g_connMap.value(self), QUERY_STATS_FLAG, request);
}

void QuitApp()
{
	exit(0);

	::TerminateProcess(::GetCurrentProcess(), 0);
}

std::string GetAppDir()
{
	std::string result = g_appDir.toStdString();

	return result;
}

std::string GetAppPath()
{
	std::string result = g_appPath.toStdString();

	return result;
}

void GetChatroomMember(std::string self, std::string roomName, std::string userName)
{
	Json::Value request;
	request["room_name"] = roomName;
	request["user_name"] = userName;

	MySendPack(g_connMap.value(self), GET_CHATROOM_MEMBER_FLAG, request);
}

std::string GetDocDir(std::string self)
{
	std::string result = g_folderMap.value(self);

	return result;
}

std::string GetWcDir()
{
	std::string result;

	HKEY hKey;
	long lRet = RegOpenKeyEx(HKEY_CURRENT_USER, L"Software\\Tencent\\WeChat", 0, KEY_QUERY_VALUE, &hKey);
	if (lRet == ERROR_SUCCESS)
	{
		DWORD dwType = 0;
		DWORD dwSize = MAX_PATH;
		char installPath[MAX_PATH] = { 0 };
		long lRet = RegQueryValueExA(hKey, "InstallPath", NULL, &dwType, (LPBYTE)installPath, &dwSize);
		if (lRet == ERROR_SUCCESS)
		{
			result = GBK_To_UTF8(installPath);
		}

		RegCloseKey(hKey);
	}

	return result;
}

std::string GetNewGuid()
{
	std::string result = QUuid::createUuid().toString().remove("-").remove("{").remove("}").toStdString().c_str();

	return result;
}

std::string GetShortName(std::string nickName, int len)
{
	std::string result;

	int size = nickName.size();
	if (size > len)
	{
		result = nickName.substr(0, len) + "*";
	}
	else
	{
		result = nickName;
	}

	return result;
}

long _GetFileSize(std::string path)
{
	long result = 0;

	FILE* file = fopen(path.c_str(), "rb");
	if (file)
	{
		result = filelength(fileno(file));
		fclose(file);
	}

	return result;
}

long _GetFileTime(std::string path)
{
	QFileInfo fileInfo(path.c_str());
	return fileInfo.lastModified().toTime_t();
}

std::string GetFileVersion(std::string path)
{
	std::string result;

	if (PathFileExistsA(path.c_str()))
	{
		DWORD dwTemp;
		DWORD dwSize = GetFileVersionInfoSizeA(path.c_str(), &dwTemp);
		if (dwSize == 0)
		{
			return "";
		}

		BYTE* pData = new BYTE[dwSize + 1];
		if (pData == NULL)
		{
			return "";
		}

		if (!GetFileVersionInfoA(path.c_str(), 0, dwSize, pData))
		{
			delete[] pData;
			return "";
		}

		VS_FIXEDFILEINFO *pVerInfo = NULL;
		UINT uLen;
		if (!VerQueryValueA(pData, "\\", (void **)&pVerInfo, &uLen))
		{
			delete[] pData;
			return "";
		}

		DWORD verMS = pVerInfo->dwFileVersionMS;
		DWORD verLS = pVerInfo->dwFileVersionLS;
		DWORD major = HIWORD(verMS);
		DWORD minor = LOWORD(verMS);
		DWORD build = HIWORD(verLS);
		DWORD revision = LOWORD(verLS);
		delete[] pData;

		std::stringstream ss;
		ss << major << "." << minor << "." << build << "." << revision;
		result = ss.str();
	}

	return result;
}

void InviteChatroomMember(std::string self, std::string roomName, std::string userName)
{
	Json::Value request;
	request["room_name"] = roomName;
	request["user_name"] = userName;

	MySendPack(g_connMap.value(self), INVITE_CHATROOM_MEMBER_FLAG, request);
}

void DelayInviteChatroomMember(std::string self, std::string roomid, std::string wxid, float seconds)
{
	DelayExec(boost::bind(&InviteChatroomMember, self, roomid, wxid), seconds * ONE_SECOND, false);
}

void CreateChatroom(std::string self, std::string wxids)
{
	Json::Value request;
	request["wxids"] = wxids;

	MySendPack(g_connMap.value(self), CREATE_CHATROOM_FLAG, request);
}

bool IsWhiteUser(std::string userName)
{
	bool isWhite = g_whiteMap.count(userName) > 0;

	return isWhite;
}

bool IsBlackUser(std::string userName)
{
	bool isWhite = g_whiteMap.count(userName) > 0;
	bool isBlack = g_blackMap.count(userName) > 0;
	if (!isWhite && isBlack)
	{
		return true;
	}

	return false;
}

void RevokeMsg(std::string self, QWORD msgSvrID, std::string sender)
{
	Json::Value request;
	request["user_name"] = sender;
	request["msg_svr_id"] = msgSvrID;

	qDebug() << self.c_str() <<  msgSvrID << sender.c_str();

	MySendPack(g_connMap.value(self), REVOKE_MSG_FLAG, request);
}

void ForwardMsg(std::string self, std::string wxid, int localID)
{
	Json::Value request;
	request["user_name"] = wxid;
	request["local_id"] = localID;

	MySendPack(g_connMap.value(self), FORWARD_MSG_FLAG, request);
}

void SendMsg(std::string self, std::string wxid, std::string text)
{
	Json::Value request;
	request["user_name"] = wxid;
	request["text"] = text;

	MySendPack(g_connMap.value(self), SEND_MSG_FLAG, request);
}

void SendGif(std::string self, std::string wxid, std::string gifPath)
{
	Json::Value request;
	request["user_name"] = wxid;
	request["file_path"] = gifPath;

	MySendPack(g_connMap.value(self), SEND_GIF_FLAG, request);
}

void SendUrl(std::string self, std::string wxid, std::string xml)
{
	Json::Value request;
	request["user_name"] = wxid;
	request["xml"] = xml;

	MySendPack(g_connMap.value(self), SEND_URL_FLAG, request);
}

void SendImg(std::string self, std::string wxid, std::string imgPath)
{
	Json::Value request;
	request["user_name"] = wxid;
	request["file_path"] = imgPath;

	MySendPack(g_connMap.value(self), SEND_IMG_FLAG, request);
}

void SendVid(std::string self, std::string wxid, std::string vidPath)
{
	Json::Value request;
	request["user_name"] = wxid;
	request["file_path"] = vidPath;



	//Json::FastWriter fastWriter;
	//std::string data = fastWriter.write(request);

	//Json::Value root;
	//Json::Reader reader;
	//reader.parse(data.c_str(), root);
	//std::string path = UTF8_To_GBK(root["file_path"].asString());





	MySendPack(g_connMap.value(self), SEND_VID_FLAG, request);
}

void SendCard(std::string self, std::string wxid, std::string xml)
{
	Json::Value request;
	request["user_name"] = wxid;
	request["xml"] = xml;

	MySendPack(g_connMap.value(self), SEND_CARD_FLAG, request);
}

void SetChatroomName(std::string self, std::string roomid, std::string name)
{
	Json::Value request;
	request["room_name"] = roomid;
	request["room_title"] = name;

	MySendPack(g_connMap.value(self), SET_CHATROOM_NAME_FLAG, request);
}

void SetChatroomAnnouncement(std::string self, std::string roomid, std::string announcement)
{
	Json::Value request;
	request["room_name"] = roomid;
	request["announcement"] = announcement;

	MySendPack(g_connMap.value(self), SET_CHATROOM_ANNOUNCEMENT_FLAG, request);
}

void SetFriendRemark(std::string self, std::string wxid, std::string remark)
{
	Json::Value request;
	request["user_name"] = wxid;
	request["remark"] = remark;

	MySendPack(g_connMap.value(self), SET_FRIEND_REMARK_FLAG, request);
}

void QuitChatroom(std::string self, std::string roomid)
{
	Json::Value request;
	request["room_name"] = roomid;

	MySendPack(g_connMap.value(self), QUIT_CHATROOM_FLAG, request);
}

void VerifyFriend(std::string self, std::string wxid)
{
	Json::Value request;
	request["user_name"] = wxid;

	MySendPack(g_connMap.value(self), QUIT_CHATROOM_FLAG, request);
}

void ShowLog(std::string text)
{
	//GBK编码
	g_pMainWindow->ShowLog(QStringLiteral("[%1] %2").arg(QDateTime::currentDateTime().toString(DATE_TIME_FORMAT)).arg(QString::fromStdString(text)));
}

void ShowMsg(std::string text)
{
	//UTF8
	MessageWindow::GetInstance().ShowMessage(QStringLiteral("提示"), QString::fromStdString(text));
}

void ShowNtc(std::string text)
{
	//UTF8
	g_pMainWindow->ShowNtc(QStringLiteral("%1").arg(QString::fromStdString(text)));
}

void _Sleep(double seconds)
{
	QEventLoop loop;
	QTimer::singleShot(seconds * ONE_SECOND, &loop, SLOT(quit()));
	loop.exec();

	//::Sleep(ONE_SECOND * seconds);
}

void WriteLog(std::string message)
{
	//std::shared_ptr<spdlog::logger> g_logger = spdlog::get("logger");
	g_logger->info(message);
}

void DelayAddFriend(std::string self, std::string wxid, std::string remark, float seconds)
{
	DelayExec(boost::bind(&AddFriend, self, wxid, remark), seconds * ONE_SECOND, false);
}

void DelayForwardMsg(std::string self, std::string wxid, int localID, float seconds)
{
	DelayExec(boost::bind(&ForwardMsg, self, wxid, localID), seconds * ONE_SECOND, false);
}

void DelaySendMsg(std::string self, std::string wxid, std::string text, float seconds)
{
	DelayExec(boost::bind(&SendMsg, self, wxid, text), seconds * ONE_SECOND, false);
}

void DelaySendUrl(std::string self, std::string wxid, std::string xml, float seconds)
{
	DelayExec(boost::bind(&SendUrl, self, wxid, xml), seconds * ONE_SECOND, false);
}

void DelaySendImg(std::string self, std::string wxid, std::string imgPath, float seconds)
{
	DelayExec(boost::bind(&SendImg, self, wxid, imgPath), seconds * ONE_SECOND, false);
}

void DelaySendVid(std::string self, std::string wxid, std::string vidPath, float seconds)
{
	DelayExec(boost::bind(&SendVid, self, wxid, vidPath), seconds * ONE_SECOND, false);
}

void DelaySendCard(std::string self, std::string wxid, std::string xml, float seconds)
{
	DelayExec(boost::bind(&SendCard, self, wxid, xml), seconds * ONE_SECOND, false);
}

void DelaySetFriendRemark(std::string self, std::string wxid, std::string remark, float seconds)
{
	DelayExec(boost::bind(&SetFriendRemark, self, wxid, remark), seconds * ONE_SECOND, false);
}

void DelayGetChatroomMember(std::string self, std::string roomName, std::string userName, float seconds)
{
	DelayExec(boost::bind(&GetChatroomMember, self, roomName, userName), seconds * ONE_SECOND, false);
}

void DelaySetChatroomAnnouncement(std::string self, std::string roomid, std::string announcement, float seconds)
{
	DelayExec(boost::bind(&SetChatroomAnnouncement, self, roomid, announcement), seconds * ONE_SECOND, false);
}

void DelayRevokeMsg(std::string self, QWORD msgSvrID, std::string sender, float seconds)
{
	DelayExec(boost::bind(&RevokeMsg, self, msgSvrID, sender), seconds * ONE_SECOND, false);
}

//https://blog.csdn.net/charlessimonyi/article/details/8722859

std::wstring UTF8_To_UTF16(const std::string &source)
{
	unsigned long len = ::MultiByteToWideChar(CP_UTF8, NULL, source.c_str(), -1, NULL, NULL);
	if (len == 0)
		return std::wstring();
	wchar_t *buffer = new wchar_t[len];
	::MultiByteToWideChar(CP_UTF8, NULL, source.c_str(), -1, buffer, len);

	std::wstring dest(buffer);
	delete[] buffer;
	return dest;
}

std::string UTF16_To_UTF8(const std::wstring &source)
{
	unsigned long len = ::WideCharToMultiByte(CP_UTF8, NULL, source.c_str(), -1, NULL, NULL, NULL, NULL);
	if (len == 0)
		return std::string();
	char *buffer = new char[len];
	::WideCharToMultiByte(CP_UTF8, NULL, source.c_str(), -1, buffer, len, NULL, NULL);

	std::string dest(buffer);
	delete[] buffer;
	return dest;
}

std::wstring GBK_To_UTF16(const std::string &source)
{
	enum { GB2312 = 936 };

	unsigned long len = ::MultiByteToWideChar(GB2312, NULL, source.c_str(), -1, NULL, NULL);
	if (len == 0)
		return std::wstring();
	wchar_t *buffer = new wchar_t[len];
	::MultiByteToWideChar(GB2312, NULL, source.c_str(), -1, buffer, len);

	std::wstring dest(buffer);
	delete[] buffer;
	return dest;
}

std::string UTF16_To_GBK(const std::wstring &source)
{
	enum { GB2312 = 936 };

	unsigned long len = ::WideCharToMultiByte(GB2312, NULL, source.c_str(), -1, NULL, NULL, NULL, NULL);
	if (len == 0)
		return std::string();
	char *buffer = new char[len];
	::WideCharToMultiByte(GB2312, NULL, source.c_str(), -1, buffer, len, NULL, NULL);

	std::string dest(buffer);
	delete[] buffer;
	return dest;
}

std::string GBK_To_UTF8(const std::string &source)
{
	enum { GB2312 = 936 };

	unsigned long len = ::MultiByteToWideChar(GB2312, NULL, source.c_str(), -1, NULL, NULL);
	if (len == 0)
		return std::string();
	wchar_t *wide_char_buffer = new wchar_t[len];
	::MultiByteToWideChar(GB2312, NULL, source.c_str(), -1, wide_char_buffer, len);

	len = ::WideCharToMultiByte(CP_UTF8, NULL, wide_char_buffer, -1, NULL, NULL, NULL, NULL);
	if (len == 0)
	{
		delete[] wide_char_buffer;
		return std::string();
	}
	char *multi_byte_buffer = new char[len];
	::WideCharToMultiByte(CP_UTF8, NULL, wide_char_buffer, -1, multi_byte_buffer, len, NULL, NULL);

	std::string dest(multi_byte_buffer);
	delete[] wide_char_buffer;
	delete[] multi_byte_buffer;
	return dest;
}

std::string UTF8_To_GBK(const std::string &source)
{
	enum { GB2312 = 936 };

	unsigned long len = ::MultiByteToWideChar(CP_UTF8, NULL, source.c_str(), -1, NULL, NULL);
	if (len == 0)
		return std::string();
	wchar_t *wide_char_buffer = new wchar_t[len];
	::MultiByteToWideChar(CP_UTF8, NULL, source.c_str(), -1, wide_char_buffer, len);

	len = ::WideCharToMultiByte(GB2312, NULL, wide_char_buffer, -1, NULL, NULL, NULL, NULL);
	if (len == 0)
	{
		delete[] wide_char_buffer;
		return std::string();
	}
	char *multi_byte_buffer = new char[len];
	::WideCharToMultiByte(GB2312, NULL, wide_char_buffer, -1, multi_byte_buffer, len, NULL, NULL);

	std::string dest(multi_byte_buffer);
	delete[] wide_char_buffer;
	delete[] multi_byte_buffer;
	return dest;
}

std::string ws2s(const std::wstring& ws)
{
	int nBufSize = WideCharToMultiByte(GetACP(), 0, ws.c_str(), -1, NULL, 0, 0, FALSE);
	char *szBuf = new char[nBufSize];
	WideCharToMultiByte(GetACP(), 0, ws.c_str(), -1, szBuf, nBufSize, 0, FALSE);
	std::string strRet(szBuf);
	delete[]szBuf;
	szBuf = NULL;
	return strRet;
}

std::wstring s2ws(const std::string& s)
{
	int nBufSize = MultiByteToWideChar(GetACP(), 0, s.c_str(), -1, NULL, 0);
	wchar_t *wsBuf = new wchar_t[nBufSize];
	MultiByteToWideChar(GetACP(), 0, s.c_str(), -1, wsBuf, nBufSize);
	std::wstring wstrRet(wsBuf);
	delete[]wsBuf;
	wsBuf = NULL;
	return wstrRet;
}

std::string& left_trim(std::string &str)
{
	return str.erase(0, str.find_first_not_of(" \t\n\r"));
}

std::string& right_trim(std::string &str)
{
	return str.erase(str.find_last_not_of(" \t\n\r") + 1);
}

std::string& trim(std::string &st)
{
	return left_trim(right_trim(st));
}

std::vector<std::string> split(const std::string& str, const std::string separator)
{
	//std::vector<std::string> strvec;
	//std::string::size_type pos1, pos2;
	//pos2 = str.find(separator);
	//pos1 = 0;

	//while (std::string::npos != pos2)
	//{
	//	strvec.push_back(str.substr(pos1, pos2 - pos1));
	//	pos1 = pos2 + separator.length();
	//	pos2 = str.find(separator, pos1);
	//}
	//strvec.push_back(str.substr(pos1));
	//return strvec;

	std::vector<std::string> items;

	std::string::size_type lastPos = str.find_first_not_of(separator, 0);
	std::string::size_type pos = str.find_first_of(separator, lastPos);
    while (std::string::npos != pos || std::string::npos != lastPos) {
		items.push_back(str.substr(lastPos, pos - lastPos));//use emplace_back after C++11
        lastPos = str.find_first_not_of(separator, pos);
        pos = str.find_first_of(separator, lastPos);
    }

	return items;
}

std::string join(std::vector<std::string>& list, std::string separator)
{
	std::string str;
	for (std::vector<std::string>::iterator it = list.begin(); it != list.end(); it++)
	{
		str += *it;
		if (it != list.end())
		{
			str += separator;
		}
	}
	return str;
}

std::string replace(std::string& s, const std::string& from, const std::string& to)
{
	std::string result = s;
	if (!from.empty())
		for (size_t pos = 0; (pos = s.find(from, pos)) != std::string::npos; pos += to.size())
			result.replace(pos, from.size(), to);
	return result;
}

bool endswith(const std::string& str, const std::string& end)
{
	int srclen = str.size();
	int endlen = end.size();
	if (srclen >= endlen)
	{
		std::string temp = str.substr(srclen - endlen, endlen);
		if (temp == end)
			return true;
	}

	return false;
}

bool startswith(const std::string& str, const std::string& start)
{
	int srclen = str.size();
	int startlen = start.size();
	if (srclen >= startlen)
	{
		std::string temp = str.substr(0, startlen);
		if (temp == start)
			return true;
	}

	return false;
}

bool contains(const std::list<std::string>& list, const std::string& str)
{
	// find_if用于自定义的相等
	return std::find(list.begin(), list.end(), str) != list.end();
}

bool CompareVersion(std::string myVersion, std::string newVersion)
{
	//newVersion是否大于myVersion
	std::vector<std::string> v1 = split(myVersion, ".");
	std::vector<std::string> v2 = split(newVersion.c_str(), ".");

	if (v1.size() != v2.size())
	{
		return false;
	}

	for (int i = 0; i < v1.size(); i++)
	{
		if (atoi(v1[i].c_str()) < atoi(v2[i].c_str()))
		{
			return true;
		}
		else if (atoi(v1[i].c_str()) > atoi(v2[i].c_str()))
		{
			return false;
		}
	}

	return false;
}

quint64 GetTimeStamp10()
{
	quint64 timeStamp = QDateTime::currentDateTime().toTime_t();
	return timeStamp;
}

quint64 GetTimeStamp13()
{
	quint64 timeStamp = QDateTime::currentDateTime().toMSecsSinceEpoch();
	return timeStamp;
}

std::string GetRandString(int length, bool isUpper, bool isLower, bool isNumber)
{
	char buffer[128] = { 0 };

	char pUpper[26] = { 0 };
	char pLower[26] = { 0 };
	char pNumber[10] = { 0 };

	for (int i = 0; i < 26; pUpper[i] = 'A' + i, i++);
	for (int i = 0; i < 26; pLower[i] = 'a' + i, i++);
	for (int i = 0; i < 10; pNumber[i] = '0' + i, i++);


	int count = 0;
	while (count <= length)
	{
		switch (rand() % 3)
		{
		case 0:
			if (isUpper)
			{
				buffer[count] = pUpper[rand() % 26];
				count++;
			}
			break;
		case 1:
			if (isLower)
			{
				buffer[count] = pLower[rand() % 26];
				count++;
			}
			break;
		case 2:
			if (isNumber)
			{
				buffer[count] = pNumber[rand() % 10];
				count++;
			}
			break;
		}
	};

	buffer[length] = 0;

	return buffer;
}

std::string GetDateString()
{
	time_t timep;
	time(&timep);

	char buffer[64];
	strftime(buffer, sizeof(buffer), "%Y%m%d", localtime(&timep));

	return buffer;
}

std::string GetDateTimeString()
{
	time_t timep;
	time(&timep);

	char buffer[64];
	strftime(buffer, sizeof(buffer), "%Y-%m-%d %H:%M:%S", localtime(&timep));

	return buffer;
}

//std::string RequestUrl(const std::string url)
//{
//	std::string result;
//
//	DWORD dwSize = 0;
//	DWORD dwDownloaded = 0;
//	LPSTR pszOutBuffer;
//	BOOL  bResults = FALSE;
//	HINTERNET  hSession = NULL;
//	HINTERNET hConnect = NULL;
//	HINTERNET hRequest = NULL;
//
//	URL_COMPONENTS urlCom;
//	memset(&urlCom, 0, sizeof(urlCom));
//	urlCom.dwStructSize = sizeof(urlCom);
//	WCHAR wchScheme[64] = { 0 };
//	urlCom.lpszScheme = wchScheme;
//	urlCom.dwSchemeLength = ARRAYSIZE(wchScheme);
//	WCHAR wchHostName[1024] = { 0 };
//	urlCom.lpszHostName = wchHostName;
//	urlCom.dwHostNameLength = ARRAYSIZE(wchHostName);
//	WCHAR wchUrlPath[1024] = { 0 };
//	urlCom.lpszUrlPath = wchUrlPath;
//	urlCom.dwUrlPathLength = ARRAYSIZE(wchUrlPath);
//	WCHAR wchExtraInfo[1024] = { 0 };
//	urlCom.lpszExtraInfo = wchExtraInfo;
//	urlCom.dwExtraInfoLength = ARRAYSIZE(wchExtraInfo);
//	WinHttpCrackUrl(s2ws(url).c_str(), url.length(), ICU_ESCAPE, &urlCom);
//
//	// Use WinHttpOpen to obtain a session handle.
//	hSession = WinHttpOpen(L"wget", WINHTTP_ACCESS_TYPE_DEFAULT_PROXY, WINHTTP_NO_PROXY_NAME, WINHTTP_NO_PROXY_BYPASS, 0);
//
//	// Specify an HTTP server.
//	if (hSession)
//	{
//		hConnect = WinHttpConnect(hSession, urlCom.lpszHostName, INTERNET_DEFAULT_HTTP_PORT, 0);	//Use INTERNET_DEFAULT_HTTPS_PORT for SSL
//	}
//
//	// Create an HTTP request handle.
//	if (hConnect)
//	{
//		std::wstring path = std::wstring(urlCom.lpszUrlPath) + std::wstring(urlCom.lpszExtraInfo);
//		hRequest = WinHttpOpenRequest(hConnect, L"GET", path.c_str(), NULL, WINHTTP_NO_REFERER, WINHTTP_DEFAULT_ACCEPT_TYPES, 0);	//Use WINHTTP_FLAG_SECURE for SSL
//	}
//
//	// Send a request.
//	if (hRequest)
//	{
//		bResults = WinHttpSendRequest(hRequest, WINHTTP_NO_ADDITIONAL_HEADERS, 0, WINHTTP_NO_REQUEST_DATA, 0, 0, 0);
//	}
//
//
//	// End the request.
//	if (bResults)
//	{
//		bResults = WinHttpReceiveResponse(hRequest, NULL);
//	}
//
//	// Keep checking for data until there is nothing left.
//	if (bResults)
//	{
//		do
//		{
//			// Check for available data.
//			dwSize = 0;
//			if (!WinHttpQueryDataAvailable(hRequest, &dwSize))
//			{
//				printf("Error %u in WinHttpQueryDataAvailable.\n", GetLastError());
//			}
//
//			// Allocate space for the buffer.
//			pszOutBuffer = new char[dwSize + 1];
//			if (!pszOutBuffer)
//			{
//				printf("Out of memory\n");
//				dwSize = 0;
//			}
//			else
//			{
//				// Read the data.
//				ZeroMemory(pszOutBuffer, dwSize + 1);
//
//				if (!WinHttpReadData(hRequest, (LPVOID)pszOutBuffer, dwSize, &dwDownloaded))
//				{
//					printf("Error %u in WinHttpReadData.\n", GetLastError());
//				}
//				else
//				{
//					//printf("%s", pszOutBuffer);
//					result += pszOutBuffer;
//				}
//
//				// Free the memory allocated to the buffer.
//				delete[] pszOutBuffer;
//			}
//		} while (dwSize > 0);
//	}
//
//	// Report any errors.
//	if (!bResults)
//	{
//		printf("Error %d has occurred.\n", GetLastError());
//	}
//
//	// Close any open handles.
//	if (hRequest) WinHttpCloseHandle(hRequest);
//	if (hConnect) WinHttpCloseHandle(hConnect);
//	if (hSession) WinHttpCloseHandle(hSession);
//
//	return result;
//}


//#include "ZLib\zlib.h"
//
//int gzCompress(const char *src, int srcLen, char *dest, int destLen)
//{
//	z_stream c_stream;
//	int err = 0;
//	int windowBits = 15;
//	int GZIP_ENCODING = 16;
//
//	if (src && srcLen > 0)
//	{
//		c_stream.zalloc = (alloc_func)0;
//		c_stream.zfree = (free_func)0;
//		c_stream.opaque = (voidpf)0;
//		if (deflateInit2(&c_stream, Z_DEFAULT_COMPRESSION, Z_DEFLATED,
//			windowBits | GZIP_ENCODING, 8, Z_DEFAULT_STRATEGY) != Z_OK) return -1;
//		c_stream.next_in = (Bytef *)src;
//		c_stream.avail_in = srcLen;
//		c_stream.next_out = (Bytef *)dest;
//		c_stream.avail_out = destLen;
//		while (c_stream.avail_in != 0 && c_stream.total_out < destLen)
//		{
//			if (deflate(&c_stream, Z_NO_FLUSH) != Z_OK) return -1;
//		}
//		if (c_stream.avail_in != 0) return c_stream.avail_in;
//		for (;;) {
//			if ((err = deflate(&c_stream, Z_FINISH)) == Z_STREAM_END) break;
//			if (err != Z_OK) return -1;
//		}
//		if (deflateEnd(&c_stream) != Z_OK) return -1;
//		return c_stream.total_out;
//	}
//	return -1;
//}
//
//// gzDecompress: do the decompressing
//int gzDecompress(const char *src, int srcLen, const char *dst, int dstLen)
//{
//	z_stream strm;
//	strm.zalloc = NULL;
//	strm.zfree = NULL;
//	strm.opaque = NULL;
//
//	strm.avail_in = srcLen;
//	strm.avail_out = dstLen;
//	strm.next_in = (Bytef *)src;
//	strm.next_out = (Bytef *)dst;
//
//	int err = -1, ret = -1;
//	err = inflateInit2(&strm, MAX_WBITS + 16);
//	if (err == Z_OK) {
//		err = inflate(&strm, Z_FINISH);
//		if (err == Z_STREAM_END) {
//			ret = strm.total_out;
//		}
//		else {
//			inflateEnd(&strm);
//			return err;
//		}
//	}
//	else {
//		inflateEnd(&strm);
//		return err;
//	}
//	inflateEnd(&strm);
//	return err;
//}
//
//#define CHECK_ERR(err, msg) { \
//    if (err != Z_OK) { \
//        fprintf(stderr, "%s error: %d\n", msg, err); \
//        exit(1); \
//    } \
//}
//
////压缩
//char* Compress(char* src, int srcLen, int* comprLen) {
//	int compressrate = 2;
//	int err;
//	int len = strlen(src) + 1;
//	std::cout << "len:" << len << ",srcLen:" << srcLen << std::endl;
//	if (len != srcLen) {
//		std::cout << "strlen != srcLen" << std::endl;
//	}
//	*comprLen = len*compressrate * sizeof(int);
//	std::cout << "ori comprLen:" << *comprLen << std::endl;
//	Byte *compr = (Byte*)calloc((uInt)(*comprLen), 1);
//	if (compr == Z_NULL) {
//		printf("out of memory\n");
//		return NULL;
//	}
//	err = compress(compr, (uLong*)comprLen, (const Bytef*)src, (uLong)len);
//	CHECK_ERR(err, "compress");
//	return (char*)compr;
//}
////解压缩
//char* Uncompress(char* compr, int comprLen, int& uncomprLen) {
//	int compressrate = 2;
//	uncomprLen = comprLen * compressrate * sizeof(int);
//	std::cout << "ori uncomprLen:" << uncomprLen << std::endl;
//	Byte *uncompr = (Byte*)calloc((uInt)(uncomprLen), 1);
//	if (uncompr == Z_NULL) {
//		printf("out of memory\n");
//		return NULL;
//	}
//	int err;
//	err = uncompress(uncompr, (uLong*)(&uncomprLen),
//		(Byte*)compr, (uLong)comprLen);
//	CHECK_ERR(err, "uncompress");
//	return (char*)uncompr;
//}
//
//int StringToHex(char *str, unsigned char *out, unsigned int *outlen)
//{
//	char *p = str;
//	char high = 0, low = 0;
//	int tmplen = strlen(p), cnt = 0;
//	tmplen = strlen(p);
//	while (cnt < (tmplen / 2))
//	{
//		high = ((*p > '9') && ((*p <= 'F') || (*p <= 'f'))) ? *p - 48 - 7 : *p - 48;
//		low = (*(++p) > '9' && ((*p <= 'F') || (*p <= 'f'))) ? *(p)-48 - 7 : *(p)-48;
//		out[cnt] = ((high & 0x0f) << 4 | (low & 0x0f));
//		p++;
//		cnt++;
//	}
//	if (tmplen % 2 != 0) out[cnt] = ((*p > '9') && ((*p <= 'F') || (*p <= 'f'))) ? *p - 48 - 7 : *p - 48;
//
//	if (outlen != NULL) *outlen = tmplen / 2 + tmplen % 2;
//	return tmplen / 2 + tmplen % 2;
//}

void RefreshStyle(QWidget *widget, const char* name, QVariant value)
{
	widget->setProperty(name, value);

	//widget->parentWidget()->style()->unpolish(widget);
	//widget->parentWidget()->style()->polish(widget);
	//widget->update();

	qApp->style()->unpolish(widget);
	qApp->style()->polish(widget);
	widget->update();
}

void LoadStyle(QWidget *widget, QString filePath)
{
	QString styleSheet;

	QFile file(filePath);
	if (file.open(QFile::ReadOnly))
	{
		styleSheet.append(QString::fromLocal8Bit(file.readAll()));

		file.close();
	}
	
	widget->setStyleSheet(styleSheet);
}

void LoadStyle(QString filePath)
{
	QString styleSheet;

	QFile file(filePath);
	if (file.open(QFile::ReadOnly))
	{
		styleSheet.append(QString::fromLocal8Bit(file.readAll()));

		file.close();
	}

	qApp->setStyleSheet(styleSheet);

}
