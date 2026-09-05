function ree_identification_two_screen()
% REE_IDENTIFICATION_TWO_SCREEN
% ACT 1: Camera/detection screen -> AI identifies the device.
% ACT 2: That screen closes and a BRAND NEW "REE Analysis Report"
%        interface opens, revealing the ideal-case REE% on a big
%        animated gauge dial.
%
% Run with:  ree_identification_two_screen

%% ---------- PALETTE ----------
BG      = [0.012 0.016 0.025];
CYAN    = [0.00 0.95 1.00];
VIOLET  = [0.55 0.35 1.00];
GREEN   = [0.10 1.00 0.45];
RED     = [1.00 0.25 0.30];
AMBER   = [1.00 0.80 0.15];
SILVER  = [0.75 0.78 0.82];
GRID    = [0.10 0.12 0.16];
PANEL   = [0.045 0.05 0.075];
monoFont = get(0,'FixedWidthFontName');

ELEM_COLORS = containers.Map( ...
    {'Nd','Pr','Dy','Tb','Sm','Y','Eu','La','Ce','Gd'}, ...
    { [0.30 0.85 1.00], [0.55 0.55 1.00], [1.00 0.55 0.25], [1.00 0.35 0.75], ...
      [0.55 1.00 0.55], [1.00 0.85 0.20], [1.00 0.45 0.45], [0.65 0.85 1.00], ...
      [0.85 0.65 1.00], [0.45 1.00 0.85] });

TH_HIGH = 5.0;   % >= HIGH -> high-value stream
TH_REC  = 1.0;   % >= REC  -> recoverable stream

%% ---------- DEVICE BANK (ideal-case %) ----------
bank = {
 'HARD DISK DRIVE (HDD)',      {'Nd','Pr','Dy','Tb'}, [4.2 1.1 0.4 0.1], 'hdd';
 'CRT / LED MONITOR PANEL',    {'Y','Eu','La','Ce'},  [2.0 0.3 1.2 0.8], 'monitor';
 'ELECTRIC MOTOR (BLDC)',      {'Nd','Pr','Dy','Sm'}, [3.5 0.9 0.6 0.3], 'motor';
 'SMARTPHONE MAIN PCB',        {'Nd','Dy','Y','Ce'},  [0.15 0.05 0.10 0.08], 'pcb';
 'FLUORESCENT / LED LAMP',     {'Y','Eu','Ce','La'},  [1.8 0.25 0.6 0.5], 'lamp';
 'WIND TURBINE MAGNET SCRAP',  {'Nd','Pr','Dy','Tb'}, [6.0 1.5 1.0 0.3], 'magnet'
};

choice = listdlg('PromptString','PLACE DEVICE UNDER CAMERA (select sample):', ...
    'SelectionMode','single','ListString',bank(:,1),'ListSize',[360 160], ...
    'Name','Device Loader');
if isempty(choice); choice = 1; end

devName   = bank{choice,1};
elemNames = bank{choice,2};
elemVals  = bank{choice,3};
iconType  = bank{choice,4};
totalREE  = sum(elemVals);
GAUGE_MAX = 10; % gauge dial scale, in %

decoyIdx = setdiff(1:size(bank,1), choice);
decoyIdx = decoyIdx(randperm(numel(decoyIdx),2));
topClasses = {devName, bank{decoyIdx(1),1}, bank{decoyIdx(2),1}};
confMain = 91 + rand()*8;
rem = 100 - confMain;
confs = [confMain, rem*0.65, rem*0.35];

%% =========================================================
%%  ACT 1 : CAMERA / DETECTION SCREEN
%% =========================================================
fig1 = figure('Name','U.M.I.N. :: IDENTIFICATION - CAMERA','NumberTitle','off', ...
    'Color',BG,'Position',[90 90 1000 720],'Resize','off');

uicontrol(fig1,'Style','text','String','U.M.I.N // AI IDENTIFICATION ENGINE - LIVE SCAN', ...
    'Units','normalized','Position',[0.03 0.955 0.94 0.035], ...
    'BackgroundColor',BG,'ForegroundColor',CYAN,'FontName',monoFont, ...
    'FontSize',13,'FontWeight','bold','HorizontalAlignment','left');
annotation(fig1,'line',[0.03 0.97],[0.945 0.945],'Color',CYAN,'LineWidth',1.2);

camAx = axes(fig1,'Units','normalized','Position',[0.05 0.30 0.9 0.62], ...
    'Color',[0.02 0.03 0.04],'XColor','none','YColor','none');
hold(camAx,'on'); axis(camAx,[0 100 0 100]);
rectangle(camAx,'Position',[0 0 100 100],'EdgeColor',CYAN,'LineWidth',1.5);
for gx = 0:20:100, plot(camAx,[gx gx],[0 100],'Color',GRID,'LineWidth',0.5); end
for gy = 0:20:100, plot(camAx,[0 100],[gy gy],'Color',GRID,'LineWidth',0.5); end
bracket(camAx,4,4,8,CYAN); bracket(camAx,96,4,-8,CYAN);
bracket(camAx,4,96,8,CYAN,true); bracket(camAx,96,96,-8,CYAN,true);
uicontrol(fig1,'Style','text','String','REC   LIVE CAMERA FEED', ...
    'Units','normalized','Position',[0.06 0.865 0.3 0.025], ...
    'BackgroundColor',[0.02 0.03 0.04],'ForegroundColor',RED,'FontName',monoFont, ...
    'FontSize',9,'FontWeight','bold','HorizontalAlignment','left');

drawIcon(camAx, iconType, 50, 46, SILVER);
boxH = rectangle(camAx,'Position',[50 46 0.1 0.1],'EdgeColor',AMBER, ...
    'LineWidth',2,'LineStyle','--','Visible','off');
labelH = text(camAx, 50, 90, '', 'Color',AMBER,'FontWeight','bold', ...
    'FontSize',11,'HorizontalAlignment','center','FontName',monoFont);
confH = text(camAx, 50, 8, '', 'Color',AMBER,'FontWeight','bold', ...
    'FontSize',10,'HorizontalAlignment','center','FontName',monoFont);

statusText = uicontrol(fig1,'Style','text','String','SYSTEM READY.', ...
    'Units','normalized','Position',[0.05 0.22 0.9 0.035], ...
    'BackgroundColor',BG,'ForegroundColor',[0.6 0.65 0.7],'FontName',monoFont, ...
    'FontSize',10,'HorizontalAlignment','left');

logBox = uicontrol(fig1,'Style','listbox','String',{}, ...
    'Units','normalized','Position',[0.05 0.04 0.9 0.16], ...
    'BackgroundColor',[0.01 0.01 0.02],'ForegroundColor',GREEN,'FontName',monoFont, ...
    'FontSize',10,'Value',1,'Enable','inactive');

drawnow;

addLog(logBox,'> BOOTING IDENTIFICATION MODULE...');
addLog(logBox,'> CAMERA FEED ACTIVE');
pause(0.4);
set(statusText,'String','DEVICE PLACED UNDER CAMERA. INITIATING DETECTION...','ForegroundColor',[0.7 0.7 0.75]);
addLog(logBox, sprintf('> DEVICE PRESENTED (hidden from model)'));
pause(0.3);

set(statusText,'String','RUNNING OBJECT DETECTOR (YOLO-style)...','ForegroundColor',CYAN);
spin(logBox,'DETECTING OBJECT');
set(boxH,'Visible','on');
for f = 1:14
    grow = f/14;
    pos = [50-30*grow, 46-35*grow, 60*grow, 70*grow];
    set(boxH,'Position',pos);
    drawnow; pause(0.02);
end
addLog(logBox,'> BOUNDING BOX LOCKED. OBJECT SEGMENTED FROM BACKGROUND.');

set(statusText,'String','RUNNING CLASSIFIER HEAD (EWasteNet-v3)...','ForegroundColor',VIOLET);
spin(logBox,'CLASSIFYING');
for f=1:12
    txt = sprintf('TOP-1: %s (%.0f%%)', topClasses{1}, confs(1)*(f/12));
    set(labelH,'String', txt);
    drawnow; pause(0.03);
end
set(labelH,'String', sprintf('%s', devName));
set(confH,'String', sprintf('CONFIDENCE: %.1f%%', confMain));
addLog(logBox, sprintf('> CLASSIFIED AS: %s (confidence %.1f%%)', devName, confMain));
addLog(logBox, sprintf('> RUNNER-UP GUESSES: %s (%.1f%%), %s (%.1f%%)', ...
    topClasses{2}, confs(2), topClasses{3}, confs(3)));
addLog(logBox,'> IDENTIFICATION LOCKED. OPENING REE ANALYSIS REPORT...');
pause(1.0);

close(fig1);

%% =========================================================
%%  ACT 2 : NEW SCREEN - REE ANALYSIS REPORT
%% =========================================================
fig2 = figure('Name','U.M.I.N. :: REE ANALYSIS REPORT','NumberTitle','off', ...
    'Color',BG,'Position',[90 60 1080 760],'Resize','off');

uicontrol(fig2,'Style','text','String','U.M.I.N // REE ANALYSIS REPORT', ...
    'Units','normalized','Position',[0.03 0.96 0.6 0.032], ...
    'BackgroundColor',BG,'ForegroundColor',AMBER,'FontName',monoFont, ...
    'FontSize',14,'FontWeight','bold','HorizontalAlignment','left');
uicontrol(fig2,'Style','text','String', sprintf('DEVICE: %s   |   CONFIDENCE: %.1f%%', devName, confMain), ...
    'Units','normalized','Position',[0.03 0.925 0.94 0.028], ...
    'BackgroundColor',BG,'ForegroundColor',[0.75 0.78 0.82],'FontName',monoFont, ...
    'FontSize',10,'HorizontalAlignment','left');
annotation(fig2,'line',[0.03 0.97],[0.915 0.915],'Color',AMBER,'LineWidth',1.2);

% ---- GAUGE DIAL (left) ----
gaugeAx = axes(fig2,'Units','normalized','Position',[0.03 0.42 0.46 0.48], ...
    'Color',BG,'XColor','none','YColor','none');
axis(gaugeAx,'equal'); hold(gaugeAx,'on'); xlim(gaugeAx,[-1.3 1.3]); ylim(gaugeAx,[-1.3 1.3]);

A_START = 200; A_END = -20;   % degree sweep (clockwise)
drawArcDeg(gaugeAx, 0,0,1.0, A_START, A_END, GRID, 14);   % background track
tickColor = [0.4 0.4 0.45];
for pct = 0:2:GAUGE_MAX
    ang = A_START + (pct/GAUGE_MAX)*(A_END-A_START);
    x1 = 1.05*cosd(ang); y1 = 1.05*sind(ang);
    x2 = 1.18*cosd(ang); y2 = 1.18*sind(ang);
    plot(gaugeAx,[x1 x2],[y1 y2],'Color',tickColor,'LineWidth',1.2);
    text(gaugeAx, 1.32*cosd(ang), 1.32*sind(ang), sprintf('%d%%',pct), ...
        'Color',tickColor,'FontSize',8,'HorizontalAlignment','center','FontName',monoFont);
end
progArc = plot(gaugeAx, 1*cosd(A_START), 1*sind(A_START),'Color',AMBER,'LineWidth',14);
gaugeBigText = text(gaugeAx, 0, 0.05, '0.00%', 'Color','w','FontSize',30, ...
    'FontWeight','bold','HorizontalAlignment','center','FontName',monoFont);
gaugeSubText = text(gaugeAx, 0, -0.28, 'IDEAL-CASE TOTAL REE CONTENT', ...
    'Color',[0.6 0.6 0.65],'FontSize',9,'HorizontalAlignment','center','FontName',monoFont);

% ---- ELEMENT BREAKDOWN (right) ----
brkPanel = uipanel(fig2,'Title','ELEMENT-WISE BREAKDOWN (IDEAL CASE)', ...
    'FontName',monoFont,'FontSize',10,'ForegroundColor',CYAN, ...
    'BackgroundColor',PANEL,'HighlightColor',GRID, ...
    'Units','normalized','Position',[0.53 0.42 0.44 0.48]);
brkAx = axes(brkPanel,'Units','normalized','Position',[0.10 0.12 0.85 0.80], ...
    'Color','none'); hold(brkAx,'on');
axis(brkAx,[0 numel(elemNames)+1 0 max(elemVals)*1.4+0.5]);
set(brkAx,'FontName',monoFont,'FontSize',8,'Color','none','XColor','none','YColor',[0.4 0.4 0.45]);
eqBars = gobjects(1,numel(elemNames)); eqLabels = gobjects(1,numel(elemNames));
for i = 1:numel(elemNames)
    c = ELEM_COLORS(elemNames{i});
    eqBars(i) = rectangle(brkAx,'Position',[i-0.35 0 0.7 0.01],'FaceColor',c,'EdgeColor','w','LineWidth',0.5);
    text(brkAx, i, -max(elemVals)*0.12, elemNames{i}, 'Color','w','FontWeight','bold', ...
        'FontSize',9,'HorizontalAlignment','center');
    eqLabels(i) = text(brkAx, i, 0.15, '0.00%', 'Color','w','FontSize',8, ...
        'HorizontalAlignment','center','FontName',monoFont);
end

% ---- ROUTING DECISION (bottom) ----
routePanel = uipanel(fig2,'Units','normalized','Position',[0.03 0.06 0.94 0.32], ...
    'BackgroundColor',PANEL,'HighlightColor',GRID,'BorderType','line');
verdictBig = uicontrol(routePanel,'Style','text','String','ANALYZING...', ...
    'Units','normalized','Position',[0.03 0.55 0.94 0.35], ...
    'BackgroundColor',PANEL,'ForegroundColor',[0.7 0.7 0.75],'FontName',monoFont, ...
    'FontSize',16,'FontWeight','bold','HorizontalAlignment','left');
verdictSub = uicontrol(routePanel,'Style','text','String','', ...
    'Units','normalized','Position',[0.03 0.15 0.94 0.35], ...
    'BackgroundColor',PANEL,'ForegroundColor',[0.6 0.62 0.66],'FontName',monoFont, ...
    'FontSize',11,'HorizontalAlignment','left');

drawnow;
pause(0.4);

%% ---- ANIMATE REVEAL ----
for f = 1:24
    tv = totalREE*(f/24);
    ang = A_START + (min(tv,GAUGE_MAX)/GAUGE_MAX)*(A_END-A_START);
    th = linspace(deg2rad(A_START), deg2rad(ang), 60);
    set(progArc,'XData', cos(th), 'YData', sin(th));
    set(gaugeBigText,'String', sprintf('%.2f%%', tv));
    drawnow; pause(0.025);
end
set(gaugeBigText,'String', sprintf('%.2f%%', totalREE));

for i = 1:numel(elemNames)
    v = elemVals(i);
    for f = 1:12
        vv = v*(f/12);
        set(eqBars(i),'Position',[i-0.35 0 0.7 max(vv,0.01)]);
        set(eqLabels(i),'Position',[i vv+max(elemVals)*0.08 0]);
        set(eqLabels(i),'String', sprintf('%.2f%%',vv));
    end
    drawnow; pause(0.05);
end

if totalREE >= TH_HIGH
    vTxt = sprintf('IN THE IDEAL CASE, THIS DEVICE CONTAINS %.2f%% RARE-EARTH ELEMENTS -> HIGH-VALUE.', totalREE);
    vSub = 'ROUTE: HIGH-VALUE STREAM -> priority hydrometallurgical extraction.';
    col = GREEN;
elseif totalREE >= TH_REC
    vTxt = sprintf('IN THE IDEAL CASE, THIS DEVICE CONTAINS %.2f%% RARE-EARTH ELEMENTS -> RECOVERABLE.', totalREE);
    vSub = 'ROUTE: RECOVERABLE STREAM -> standard extraction batch.';
    col = CYAN;
else
    vTxt = sprintf('IN THE IDEAL CASE, THIS DEVICE CONTAINS %.2f%% RARE-EARTH ELEMENTS -> LOW YIELD.', totalREE);
    vSub = 'ROUTE: LOW-YIELD / SCRAP STREAM -> conventional metal recovery only.';
    col = [0.65 0.65 0.7];
end
set(verdictBig,'String', vTxt, 'ForegroundColor', col);
set(verdictSub,'String', vSub);
set(progArc,'Color', col);
set(gaugeBigText,'Color', col);

fprintf('\n=== REE IDENTIFICATION REPORT ===\n');
fprintf('Device: %s | Confidence: %.1f%%\n', devName, confMain);
for i = 1:numel(elemNames)
    fprintf('  %s : %.2f%%\n', elemNames{i}, elemVals(i));
end
fprintf('TOTAL REE (ideal case): %.2f%%\n', totalREE);

end

%% ================= HELPER FUNCTIONS =================
function addLog(logBox, msg)
    cur = get(logBox,'String');
    cur{end+1} = msg;
    set(logBox,'String',cur);
    set(logBox,'ListboxTop', max(1, numel(cur)-6));
    drawnow; pause(0.25);
end

function spin(logBox, label)
    chars = {'|','/','-','\'};
    for s = 1:8
        cur = get(logBox,'String');
        msg = sprintf('  %s %s...', chars{mod(s-1,4)+1}, label);
        if ~isempty(cur) && startsWith(strtrim(cur{end}), {'|','/','-','\'})
            cur{end} = msg;
        else
            cur{end+1} = msg;
        end
        set(logBox,'String',cur);
        set(logBox,'ListboxTop', max(1, numel(cur)-6));
        drawnow; pause(0.06);
    end
end

function bracket(ax, x, y, s, color, flip)
    if nargin < 6; flip = false; end
    L = abs(s); sgn = sign(s);
    if ~flip
        plot(ax,[x x+L*sgn],[y y],'Color',color,'LineWidth',2.5);
        plot(ax,[x x],[y y+L],'Color',color,'LineWidth',2.5);
    else
        plot(ax,[x x+L*sgn],[y y],'Color',color,'LineWidth',2.5);
        plot(ax,[x x],[y y-L],'Color',color,'LineWidth',2.5);
    end
end

function drawArcDeg(ax, cx, cy, r, a1deg, a2deg, color, lw)
    th = linspace(deg2rad(a1deg), deg2rad(a2deg), 100);
    plot(ax, cx+r*cos(th), cy+r*sin(th), 'Color', color, 'LineWidth', lw);
end

function drawIcon(ax, type, xc, yc, color)
switch type
    case 'hdd'
        rectangle(ax,'Position',[xc-22 yc-16 44 32],'FaceColor',[0.15 0.15 0.18], ...
            'EdgeColor',color,'LineWidth',1.5,'Curvature',0.05);
        rectangle(ax,'Position',[xc-14 yc-10 28 20],'Curvature',[1 1], ...
            'FaceColor',[0.55 0.6 0.65],'EdgeColor',color);
        plot(ax,[xc-2 xc+16],[yc+6 yc-8],'Color',[0.9 0.7 0.2],'LineWidth',2);
    case 'monitor'
        rectangle(ax,'Position',[xc-24 yc-4 48 30],'FaceColor',[0.1 0.1 0.15], ...
            'EdgeColor',color,'LineWidth',1.5);
        rectangle(ax,'Position',[xc-6 yc-16 12 12],'FaceColor',[0.2 0.2 0.25],'EdgeColor',color);
        rectangle(ax,'Position',[xc-16 yc-20 32 4],'FaceColor',[0.2 0.2 0.25],'EdgeColor',color);
    case 'motor'
        rectangle(ax,'Position',[xc-16 yc-16 32 32],'Curvature',[1 1], ...
            'FaceColor',[0.2 0.2 0.25],'EdgeColor',color,'LineWidth',1.5);
        rectangle(ax,'Position',[xc-6 yc-6 12 12],'Curvature',[1 1], ...
            'FaceColor',[0.5 0.55 0.6],'EdgeColor',color);
        plot(ax,[xc+16 xc+26],[yc yc],'Color',[0.6 0.6 0.65],'LineWidth',4);
    case 'pcb'
        rectangle(ax,'Position',[xc-22 yc-16 44 32],'FaceColor',[0.05 0.25 0.1], ...
            'EdgeColor',color,'LineWidth',1.5);
        for gx2 = -16:8:16
            rectangle(ax,'Position',[xc+gx2-2 yc-2 4 4],'FaceColor',[0.7 0.7 0.2],'EdgeColor','none');
        end
        for gy2 = -8:8:8
            plot(ax,[xc-20 xc+20],[yc+gy2 yc+gy2],'Color',[0.6 0.6 0.6],'LineWidth',0.5);
        end
    case 'lamp'
        rectangle(ax,'Position',[xc-10 yc-4 20 24],'Curvature',[1 1], ...
            'FaceColor',[1 1 0.85],'EdgeColor',color,'LineWidth',1.5);
        rectangle(ax,'Position',[xc-6 yc-16 12 12],'FaceColor',[0.6 0.6 0.6],'EdgeColor',color);
    case 'magnet'
        patch(ax,'XData',[xc-20 xc+18 xc+22 xc-8],'YData',[yc-14 yc-16 yc+14 yc+18], ...
            'FaceColor',[0.35 0.35 0.4],'EdgeColor',color,'LineWidth',1.5);
        for st = -12:8:12
            plot(ax,[xc-14+st xc-10+st],[yc-10 yc+10],'Color',[0.7 0.2 0.2],'LineWidth',2);
        end
    otherwise
        rectangle(ax,'Position',[xc-18 yc-18 36 36],'FaceColor',[0.2 0.2 0.25],'EdgeColor',color);
end
end