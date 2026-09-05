function ree_identification_simulation_hud()
% REE_IDENTIFICATION_SIMULATION_HUD
% Stage 2 of the U.M.I.N pipeline: IDENTIFICATION
%   -> device is "shown" to the camera
%   -> AI object-detector draws a bounding box + classifies the device
%   -> ideal-case REE% composition for that device class is revealed
%   -> routing decision is made based on total REE content
%
% Run with:  ree_identification_simulation_hud

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

%% ---------- ROUTING THRESHOLDS (total REE % by weight) ----------
TH_HIGH = 5.0;   % >= HIGH  -> high-value stream
TH_REC  = 1.0;   % >= REC   -> recoverable stream
                 % < REC    -> scrap stream

%% ---------- DEVICE / REFERENCE DATA BANK (ideal-case %) ----------
% name, elements(cell), values(vector, % by weight), icon type
bank = {
 'HARD DISK DRIVE (HDD)',      {'Nd','Pr','Dy','Tb'}, [4.2 1.1 0.4 0.1], 'hdd';
 'CRT / LED MONITOR PANEL',    {'Y','Eu','La','Ce'},  [2.0 0.3 1.2 0.8], 'monitor';
 'ELECTRIC MOTOR (BLDC)',      {'Nd','Pr','Dy','Sm'}, [3.5 0.9 0.6 0.3], 'motor';
 'SMARTPHONE MAIN PCB',        {'Nd','Dy','Y','Ce'},  [0.15 0.05 0.10 0.08], 'pcb';
 'FLUORESCENT / LED LAMP',     {'Y','Eu','Ce','La'},  [1.8 0.25 0.6 0.5], 'lamp';
 'WIND TURBINE MAGNET SCRAP',  {'Nd','Pr','Dy','Tb'}, [6.0 1.5 1.0 0.3], 'magnet'
};

names = bank(:,1);
choice = listdlg('PromptString','PLACE DEVICE UNDER CAMERA (select sample):', ...
    'SelectionMode','single','ListString',names,'ListSize',[360 160], ...
    'Name','Device Loader');
if isempty(choice); choice = 1; end

devName   = bank{choice,1};
elemNames = bank{choice,2};
elemVals  = bank{choice,3};
iconType  = bank{choice,4};
totalREE  = sum(elemVals);

% pick 2 decoy classes for the AI's "top-3" readout
decoyIdx = setdiff(1:size(bank,1), choice);
decoyIdx = decoyIdx(randperm(numel(decoyIdx),2));
topClasses = {devName, bank{decoyIdx(1),1}, bank{decoyIdx(2),1}};
confMain = 91 + rand()*8;              % 91-99%
rem = 100 - confMain;
confs = [confMain, rem*0.65, rem*0.35];

%% ---------- FIGURE ----------
fig = figure('Name','U.M.I.N. :: IDENTIFICATION MODULE','NumberTitle','off', ...
    'Color',BG,'Position',[60 30 1120 800],'Resize','off');

uicontrol(fig,'Style','text','String','U.M.I.N // AI IDENTIFICATION ENGINE', ...
    'Units','normalized','Position',[0.03 0.965 0.55 0.03], ...
    'BackgroundColor',BG,'ForegroundColor',CYAN,'FontName',monoFont, ...
    'FontSize',13,'FontWeight','bold','HorizontalAlignment','left');
uicontrol(fig,'Style','text','String','MODEL: EWasteNet-v3  |  LAB: VIT graVITas AI  |  STATUS: ONLINE', ...
    'Units','normalized','Position',[0.55 0.965 0.42 0.03], ...
    'BackgroundColor',BG,'ForegroundColor',GREEN,'FontName',monoFont, ...
    'FontSize',9,'FontWeight','bold','HorizontalAlignment','right');
annotation(fig,'line',[0.03 0.97],[0.955 0.955],'Color',CYAN,'LineWidth',1.2);

%% ---------- LEFT: CAMERA VIEWPORT ----------
camAx = axes(fig,'Units','normalized','Position',[0.03 0.50 0.55 0.44], ...
    'Color',[0.02 0.03 0.04],'XColor','none','YColor','none');
hold(camAx,'on'); axis(camAx,[0 100 0 100]);
rectangle(camAx,'Position',[0 0 100 100],'EdgeColor',CYAN,'LineWidth',1.5);

% viewfinder grid
for gx = 0:20:100
    plot(camAx,[gx gx],[0 100],'Color',GRID,'LineWidth',0.5);
end
for gy = 0:20:100
    plot(camAx,[0 100],[gy gy],'Color',GRID,'LineWidth',0.5);
end
% AR corner brackets (camera frame)
bracket(camAx,4,4,8,CYAN); bracket(camAx,96,4,-8,CYAN);
bracket(camAx,4,96,8,CYAN,true); bracket(camAx,96,96,-8,CYAN,true);

uicontrol(fig,'Style','text','String','REC   LIVE CAMERA FEED', ...
    'Units','normalized','Position',[0.045 0.895 0.3 0.025], ...
    'BackgroundColor',[0.02 0.03 0.04],'ForegroundColor',RED,'FontName',monoFont, ...
    'FontSize',9,'FontWeight','bold','HorizontalAlignment','left');

drawIcon(camAx, iconType, 50, 48, SILVER);

boxH = rectangle(camAx,'Position',[20 15 60 70],'EdgeColor',AMBER, ...
    'LineWidth',2,'LineStyle','--','Visible','off');
labelH = text(camAx, 50, 88, '', 'Color',AMBER,'FontWeight','bold', ...
    'FontSize',10,'HorizontalAlignment','center','FontName',monoFont);
confH = text(camAx, 50, 10, '', 'Color',AMBER,'FontWeight','bold', ...
    'FontSize',9,'HorizontalAlignment','center','FontName',monoFont);

%% ---------- RIGHT: CLASSIFIER OUTPUT ----------
clsPanel = uipanel(fig,'Title','AI CLASSIFIER OUTPUT - TOP-3 PREDICTIONS', ...
    'FontName',monoFont,'FontSize',10,'ForegroundColor',VIOLET, ...
    'BackgroundColor',PANEL,'HighlightColor',GRID, ...
    'Units','normalized','Position',[0.60 0.50 0.37 0.44]);

clsAx = axes(clsPanel,'Units','normalized','Position',[0.06 0.08 0.90 0.80], ...
    'Color','none'); hold(clsAx,'on');
axis(clsAx,[0 100 0 3]); set(clsAx,'YDir','reverse');
set(clsAx,'Color','none','FontName',monoFont,'FontSize',8,'XColor',[0.4 0.4 0.45],'YColor','none');
clsAx.XTick = [0 25 50 75 100];

barH = gobjects(1,3); txtH = gobjects(1,3);
barColors = {VIOLET, [0.4 0.4 0.5], [0.3 0.3 0.4]};
for i = 1:3
    rectangle(clsAx,'Position',[0 i-0.85 100 0.7],'FaceColor',[1 1 1 0.03],'EdgeColor','none');
    barH(i) = rectangle(clsAx,'Position',[0 i-0.85 0.01 0.7], ...
        'FaceColor',barColors{i},'EdgeColor','none');
    txtH(i) = text(clsAx, 2, i-0.5, sprintf('%s',topClasses{i}), ...
        'Color','w','FontSize',8,'FontName',monoFont,'FontWeight','bold');
end

%% ---------- SPINNER / STATUS LINE ----------
statusText = uicontrol(fig,'Style','text','String','SYSTEM READY.', ...
    'Units','normalized','Position',[0.03 0.455 0.94 0.03], ...
    'BackgroundColor',BG,'ForegroundColor',[0.6 0.65 0.7],'FontName',monoFont, ...
    'FontSize',9,'HorizontalAlignment','left');

%% ---------- TERMINAL LOG ----------
uicontrol(fig,'Style','text','String','>> SYSTEM LOG', ...
    'Units','normalized','Position',[0.03 0.415 0.4 0.025], ...
    'BackgroundColor',BG,'ForegroundColor',[0.5 0.55 0.6],'FontName',monoFont, ...
    'FontSize',9,'HorizontalAlignment','left');
logBox = uicontrol(fig,'Style','listbox','String',{}, ...
    'Units','normalized','Position',[0.03 0.28 0.94 0.135], ...
    'BackgroundColor',[0.01 0.01 0.02],'ForegroundColor',GREEN,'FontName',monoFont, ...
    'FontSize',10,'Value',1,'Enable','inactive');

%% ---------- BOTTOM: REE COMPOSITION EQUALIZER ----------
reePanel = uipanel(fig,'Title','IDEAL-CASE REE COMPOSITION - DETECTED DEVICE', ...
    'FontName',monoFont,'FontSize',10,'ForegroundColor',CYAN, ...
    'BackgroundColor',PANEL,'HighlightColor',GRID, ...
    'Units','normalized','Position',[0.03 0.09 0.94 0.18]);

reeAx = axes(reePanel,'Units','normalized','Position',[0.05 0.15 0.68 0.75], ...
    'Color','none'); hold(reeAx,'on');
axis(reeAx,[0 numel(elemNames)+1 0 max(elemVals)*1.4+0.5]);
set(reeAx,'FontName',monoFont,'FontSize',8,'Color','none','XColor','none','YColor',[0.4 0.4 0.45]);

eqBars = gobjects(1,numel(elemNames)); eqLabels = gobjects(1,numel(elemNames));
for i = 1:numel(elemNames)
    c = ELEM_COLORS(elemNames{i});
    eqBars(i) = rectangle(reeAx,'Position',[i-0.35 0 0.7 0.01], ...
        'FaceColor',c,'EdgeColor','w','LineWidth',0.5);
    text(reeAx, i, -max(elemVals)*0.12, elemNames{i}, 'Color','w', ...
        'FontWeight','bold','FontSize',9,'HorizontalAlignment','center');
    eqLabels(i) = text(reeAx, i, 0.15, '0.00%', 'Color','w','FontSize',8, ...
        'HorizontalAlignment','center','FontName',monoFont);
end

totalBadge = uicontrol(reePanel,'Style','text','String','TOTAL REE: --.--%', ...
    'Units','normalized','Position',[0.76 0.55 0.22 0.35], ...
    'BackgroundColor',PANEL,'ForegroundColor',AMBER,'FontName',monoFont, ...
    'FontSize',15,'FontWeight','bold','HorizontalAlignment','center');
routeBadge = uicontrol(reePanel,'Style','text','String','ROUTE: PENDING', ...
    'Units','normalized','Position',[0.76 0.12 0.22 0.35], ...
    'BackgroundColor',PANEL,'ForegroundColor',[0.6 0.6 0.65],'FontName',monoFont, ...
    'FontSize',11,'FontWeight','bold','HorizontalAlignment','center');

drawnow;

%% ================= SIMULATION SEQUENCE =================
addLog('> BOOTING IDENTIFICATION MODULE...');
addLog('> CAMERA FEED ACTIVE (1080p, 30fps simulated)');
pause(0.4);
setStatus('DEVICE PLACED UNDER CAMERA. INITIATING DETECTION...', [0.7 0.7 0.75]);
addLog(sprintf('> DEVICE PRESENTED: %s (ground-truth, hidden from model)', devName));
pause(0.3);

setStatus('RUNNING OBJECT DETECTOR (YOLO-style)...', CYAN);
spin('DETECTING OBJECT');
set(boxH,'Visible','on');
for f = 1:12
    grow = f/12;
    pos = [50-30*grow, 50-35*grow, 60*grow, 70*grow];
    set(boxH,'Position',pos);
    drawnow; pause(0.02);
end
addLog('> BOUNDING BOX LOCKED. OBJECT SEGMENTED FROM BACKGROUND.');

setStatus('RUNNING CLASSIFIER HEAD (EWasteNet-v3)...', VIOLET);
spin('CLASSIFYING');
for f = 1:15
    for i = 1:3
        w = confs(i) * (f/15);
        set(barH(i),'Position',[0 i-0.85 max(w,0.01) 0.7]);
    end
    drawnow; pause(0.03);
end
for i = 1:3
    set(txtH(i),'String', sprintf('%-28s %5.1f%%', topClasses{i}, confs(i)));
end
set(labelH,'String', sprintf('%s', devName));
set(confH,'String', sprintf('CONFIDENCE: %.1f%%', confMain));
addLog(sprintf('> CLASSIFIED AS: %s  (confidence %.1f%%)', devName, confMain));
addLog(sprintf('> RUNTIME: %d ms  |  MODEL: EWasteNet-v3  |  DEVICE: simulated-GPU', 30+round(rand()*25)));
pause(0.4);

setStatus('CROSS-REFERENCING MATERIAL COMPOSITION DATABASE...', AMBER);
spin('LOOKING UP REE TABLE');
for i = 1:numel(elemNames)
    v = elemVals(i);
    for f = 1:14
        vv = v*(f/14);
        set(eqBars(i),'Position',[i-0.35 0 0.7 max(vv,0.01)]);
        set(eqLabels(i),'Position',[i vv+max(elemVals)*0.08 0]);
        set(eqLabels(i),'String', sprintf('%.2f%%',vv));
    end
    drawnow; pause(0.05);
end
addLog(sprintf('> COMPOSITION LOOKUP COMPLETE: %s', strjoin( ...
    arrayfun(@(i) sprintf('%s=%.2f%%',elemNames{i},elemVals(i)), 1:numel(elemNames), 'UniformOutput',false), ', ')));

for f = 1:14
    tv = totalREE*(f/14);
    set(totalBadge,'String', sprintf('TOTAL REE: %.2f%%', tv));
    drawnow; pause(0.03);
end
set(totalBadge,'String', sprintf('TOTAL REE: %.2f%%', totalREE));

if totalREE >= TH_HIGH
    routeStr = 'ROUTE: HIGH-VALUE STREAM'; routeCol = GREEN;
    routeMsg = 'High REE yield -> priority hydrometallurgical extraction.';
elseif totalREE >= TH_REC
    routeStr = 'ROUTE: RECOVERABLE STREAM'; routeCol = CYAN;
    routeMsg = 'Moderate REE yield -> standard extraction batch.';
else
    routeStr = 'ROUTE: LOW-YIELD / SCRAP'; routeCol = [0.6 0.6 0.65];
    routeMsg = 'Low REE yield -> conventional scrap/metal recovery only.';
end
set(routeBadge,'String', routeStr,'ForegroundColor', routeCol);
addLog(sprintf('> %s (%.2f%% total REE)', routeStr, totalREE));
setStatus(sprintf('IDENTIFICATION COMPLETE - %s', routeMsg), routeCol);
addLog('> PASSING RESULT TO STAGE 3: SEGREGATION.');

fprintf('\n=== REE IDENTIFICATION REPORT ===\n');
fprintf('Device: %s | Confidence: %.1f%%\n', devName, confMain);
for i = 1:numel(elemNames)
    fprintf('  %s : %.2f%%\n', elemNames{i}, elemVals(i));
end
fprintf('TOTAL REE: %.2f%% -> %s\n', totalREE, routeStr);

%% ================= NESTED HELPERS =================
    function addLog(msg)
        cur = get(logBox,'String');
        cur{end+1} = msg;
        set(logBox,'String',cur);
        set(logBox,'ListboxTop', max(1, numel(cur)-6));
        drawnow; pause(0.25);
    end

    function setStatus(msg, color)
        set(statusText,'String', msg, 'ForegroundColor', color);
        drawnow;
    end

    function spin(label)
        chars = {'|','/','-','\'};
        for s = 1:8
            addLogNoWait(sprintf('  %s %s...', chars{mod(s-1,4)+1}, label));
        end
    end

    function addLogNoWait(msg)
        cur = get(logBox,'String');
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

%% ================= STANDALONE HELPERS =================
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

function drawIcon(ax, type, xc, yc, color)
% simple vector "silhouette" icons standing in for a real camera image
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